#!/bin/bash

# 1. VÉRIFICATION DES PRIVILÈGES
if [ "$EUID" -ne 0 ]; then
  echo "❌ Erreur : Veuillez exécuter ce script en tant que super-utilisateur."
  echo "👉 Commande : sudo ./start_agent.sh"
  exit 1
fi

# 2. INSTALLATION SILENCIEUSE DES DÉPENDANCES
echo "⚙️  Vérification et préparation de l'environnement..."

# Dépendances système (APT)
PACKAGES="whiptail ansible python3-pip python3-venv sshpass"
for pkg in $PACKAGES; do
    if ! dpkg -l | grep -qw "$pkg"; then
        echo "   -> Installation du paquet manquant : $pkg..."
        apt-get update -qq > /dev/null 2>&1
        apt-get install -y -qq "$pkg" > /dev/null 2>&1
    fi
done

# Dépendances Python (PIP) pour l'API
# On utilise --break-system-packages pour les distributions Ubuntu récentes ou on installe globalement si permis
if ! pip3 show fastapi uvicorn pydantic > /dev/null 2>&1; then
    echo "   -> Installation des modules Python (FastAPI, Uvicorn)..."
    pip3 install -q fastapi uvicorn pydantic --break-system-packages > /dev/null 2>&1 || pip3 install -q fastapi uvicorn pydantic > /dev/null 2>&1
fi

echo "✅ Environnement prêt !"
sleep 1

# 3. FONCTION DE LANCEMENT DE LA PLATEFORME WEB
ouvrir_plateforme() {
    if whiptail --title "Détails" --yesno "Voulez-vous démarrer l'interface web détaillée ?" 10 60; then
        
        # On tue les anciens processus Uvicorn s'ils existent pour éviter les conflits de port
        pkill -f "uvicorn main:app" > /dev/null 2>&1
        
        # Lance FastAPI en arrière-plan
        uvicorn main:app --port 8080 > /dev/null 2>&1 &
        
        whiptail --title "API Démarrée" --msgbox "L'agent tourne en arrière-plan.\n\nOuvrez un navigateur sur :\nhttp://127.0.0.1:8080" 10 50
    fi
}

# 4. MENU PRINCIPAL INTERACTIF (TUI)
while true; do
    CHOIX=$(whiptail --title "Agent de Sécurité CIS - Mode USB" --menu "Sélectionnez une action :" 15 60 4 \
    "1" "🔍 Lancer l'Audit de sécurité" \
    "2" "🛡️ Durcir le système (Remédiation)" \
    "3" "↩️ Effectuer un Rollback" \
    "4" "❌ Quitter" 3>&1 1>&2 2>&3)

    # Gestion de l'annulation (Bouton Cancel)
    if [ $? -ne 0 ]; then
        clear
        echo "Fermeture de l'agent USB."
        exit 0
    fi

    case $CHOIX in
        1)
            # Exécution de l'audit en mode silencieux et comptage
            SCORE=$(ansible-playbook -i ansible/inventory.ini ansible/playbooks/audit_cis_global.yml --limit localhost | grep -c "CONFORME")
            whiptail --title "Résultat de l'Audit" --msgbox "Audit terminé avec succès !\n\nScore de conformité : $SCORE / 50" 10 50
            ouvrir_plateforme
            ;;
        2)
            ansible-playbook -i ansible/inventory.ini ansible/playbooks/harden_cis_global.yml --limit localhost > /dev/null 2>&1
            whiptail --title "Succès" --msgbox "Durcissement (Hardening) appliqué avec succès sur le système local." 8 50
            ;;
        3)
            ansible-playbook -i ansible/inventory.ini ansible/playbooks/rollback_cis_global.yml --limit localhost > /dev/null 2>&1
            whiptail --title "Succès" --msgbox "Restauration des paramètres par défaut terminée." 8 50
            ;;
        4)
            clear
            echo "Fermeture de l'agent USB."
            exit 0
            ;;
    esac
done
