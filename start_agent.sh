#!/bin/bash

# 1. VÉRIFICATION DES PRIVILÈGES
if [ "$EUID" -ne 0 ]; then
  echo "❌ Erreur : Veuillez exécuter ce script en tant que super-utilisateur."
  echo "👉 Commande : sudo ./start_agent.sh"
  exit 1
fi

# 2. INSTALLATION SILENCIEUSE DES DÉPENDANCES
echo "⚙️  Vérification et préparation de l'environnement..."

PACKAGES="whiptail ansible python3-pip python3-venv sshpass"
for pkg in $PACKAGES; do
    if ! dpkg -l | grep -qw "$pkg"; then
        echo "   -> Installation du paquet manquant : $pkg..."
        apt-get update -qq > /dev/null 2>&1
        apt-get install -y -qq "$pkg" > /dev/null 2>&1
    fi
done

if ! pip3 show fastapi uvicorn pydantic > /dev/null 2>&1; then
    echo "   -> Installation des modules Python (FastAPI, Uvicorn)..."
    pip3 install -q fastapi uvicorn pydantic --break-system-packages > /dev/null 2>&1 || pip3 install -q fastapi uvicorn pydantic > /dev/null 2>&1
fi

# 3. CONFIGURATION DYNAMIQUE DES IDENTIFIANTS (INVENTORY.INI)
USER_CIBLE=$(whiptail --title "Configuration de l'Agent" --inputbox "Entrez le nom d'utilisateur administrateur sur cette machine :" 10 60 "root" 3>&1 1>&2 2>&3)
if [ $? -ne 0 ]; then clear; echo "Annulé."; exit 0; fi

PASS_CIBLE=$(whiptail --title "Configuration de l'Agent" --passwordbox "Entrez le mot de passe sudo/root pour '$USER_CIBLE' :" 10 60 3>&1 1>&2 2>&3)
if [ $? -ne 0 ]; then clear; echo "Annulé."; exit 0; fi

mkdir -p ansible
cat << EOF > ansible/inventory.ini
[servers]
localhost ansible_connection=local ansible_user=$USER_CIBLE ansible_become_pass='$PASS_CIBLE'
EOF

echo "✅ Environnement et inventaire prêts !"

# =================================================================
# 4. ALLUMAGE AUTOMATIQUE DE LA PLATEFORME WEB EN ARRIÈRE-PLAN
# =================================================================
echo "🚀 Démarrage de l'interface Web..."
pkill -f "uvicorn" > /dev/null 2>&1

if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Lancement silencieux en arrière-plan (&)
uvicorn backend.main:app --host 0.0.0.0 --port 8080 --reload > /dev/null 2>&1 &

IP_SERVEUR=$(hostname -I | awk '{print $1}')
[ -z "$IP_SERVEUR" ] && IP_SERVEUR="127.0.0.1"

# Petite pause pour laisser le temps au serveur de démarrer
sleep 2 

# 5. MENU PRINCIPAL INTERACTIF (TUI)
while true; do
    CHOIX=$(whiptail --title "Agent de Sécurité CIS - Mode USB" --menu "Sélectionnez une action :" 16 70 5 \
    "1" "🔍 Lancer l'Audit (Afficher la progression live)" \
    "2" "🛡️ Durcir le système (Afficher la progression live)" \
    "3" "↩️ Effectuer un Rollback (Afficher progression live)" \
    "4" "🌐 Afficher les liens d'accès à l'Interface Web" \
    "5" "❌ Quitter" 3>&1 1>&2 2>&3)

    if [ $? -ne 0 ]; then
        clear
        echo "Fermeture de l'agent USB."
        exit 0
    fi

    case $CHOIX in
        1)
            clear
            echo "================================================================"
            echo " 🔍 Lancement de l'Audit de Sécurité CIS..."
            echo "================================================================"
            ansible-playbook -i ansible/inventory.ini ansible/playbooks/audit_cis_global.yml --limit localhost
            echo ""
            read -p "👉 Appuyez sur [Entrée] pour retourner au menu principal..."
            ;;
        2)
            clear
            echo "================================================================"
            echo " 🛡️ Application du Durcissement (Hardening)..."
            echo "================================================================"
            ansible-playbook -i ansible/inventory.ini ansible/playbooks/harden_cis_global.yml --limit localhost
            echo ""
            read -p "👉 Appuyez sur [Entrée] pour retourner au menu principal..."
            ;;
        3)
            clear
            echo "================================================================"
            echo " ↩️ Restauration des paramètres (Rollback)..."
            echo "================================================================"
            ansible-playbook -i ansible/inventory.ini ansible/playbooks/rollback_cis_global.yml --limit localhost
            echo ""
            read -p "👉 Appuyez sur [Entrée] pour retourner au menu principal..."
            ;;
        4)
            whiptail --title "Interface Web Active" --msgbox "L'API et le serveur web tournent déjà en arrière-plan.\n\n🌐 Accès direct sur cette machine :\nhttp://127.0.0.1:8080\n\n🌐 Accès depuis un autre poste du réseau :\nhttp://$IP_SERVEUR:8080" 13 65
            ;;
        5)
            clear
            echo "Fermeture de l'agent USB."
            # Optionnel : Tuer le serveur web à la fermeture du menu si vous le souhaitez
            # pkill -f "uvicorn" > /dev/null 2>&1
            exit 0
            ;;
    esac
done
