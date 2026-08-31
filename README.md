# CIS_Project
# 🛡️ Plateforme de Hardening CIS - Agent Local & TUI USB

Une plateforme automatisée d'audit et de remédiation (Hardening) basée sur les standards de sécurité CIS (Center for Internet Security), conçue pour les environnements Linux (Ubuntu/Debian). 

Ce projet propose un agent local hybride : il peut être déployé via une clé USB pour des interventions physiques avec une interface terminal interactive (TUI), ou piloté via un tableau de bord Web moderne.

## ✨ Fonctionnalités Principales

* **🔍 Audit Automatisé (Live) :** Vérification instantanée de 50 règles de sécurité critiques (Permissions, Services SSH, Configuration Réseau, Logging, Contrôle d'accès) avec affichage de la progression en temps réel.
* **🛡️ Durcissement (Hardening) :** Remédiation automatisée des vulnérabilités en un clic via des playbooks Ansible idempotents.
* **💾 Sauvegarde & Rollback Intelligent :** Création automatique d'une archive (`.tar.gz`) de l'état initial de la machine avant toute modification. Le Rollback permet une restauration système parfaite et sécurisée en cas de besoin.
* **🔌 Déploiement "Plug & Play" :** Script d'installation autonome qui installe les dépendances manquantes silencieusement, configure dynamiquement les identifiants locaux, et lance l'API en arrière-plan.
* **🌐 Tableau de Bord Web :** Interface graphique fluide et responsive permettant de visualiser le score global et le détail de conformité.

## 🛠️ Architecture & Stack Technique

* **Backend API :** Python 3, FastAPI, Uvicorn (Asynchrone)
* **Orchestration & Sécurité :** Ansible (Connexion locale stricte)
* **Frontend Web :** HTML5, Tailwind CSS, JavaScript (Vanilla)
* **Interface Terminal (TUI) :** Bash, Whiptail

## 🚀 Installation & Utilisation

L'outil est conçu pour s'adapter dynamiquement à n'importe quelle machine cible (bare-metal ou VM).

1. Clonez ce dépôt sur votre machine (ou copiez-le sur une clé USB).
2. Positionnez-vous à la racine du projet et exécutez le lanceur avec les privilèges administrateur :
   ```bash
   sudo chmod +x start_agent.sh
   sudo ./start_agent.sh

#STRUCTURE DU PROJET 

CIS_Project/
├── ansible/
│   ├── inventory.ini             # Généré dynamiquement par le script
│   ├── playbooks/                # Orchestrateurs (audit, harden, rollback)
│   └── tasks/                    # Règles CIS découpées par section (01 à 05)
├── frontend/
│   └── index.html                # Tableau de bord graphique de l'agent
├── main.py                       # Backend FastAPI (Logique et routes)
└── start_agent.sh                # Lanceur interactif Bash (Menu principal)

🎓 Auteur

Abdessamad Idhamouch

Ingénierie en Cybersécurité (4ème année) - École Marocaine des Sciences de l'Ingénieur (EMSI)
