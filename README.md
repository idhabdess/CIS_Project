# 🛡️ Plateforme de Hardening CIS - Agent Local & USB

Une plateforme automatisée d'audit et de remédiation (Hardening) basée sur les standards de sécurité CIS (Center for Internet Security), conçue pour les environnements Linux (Ubuntu/Debian). 

Ce projet propose un agent local hybride : il peut être déployé via une clé USB pour des interventions physiques avec une interface terminal (TUI), ou piloté via un tableau de bord Web moderne.

## ✨ Fonctionnalités Principales

* **🔍 Audit Automatisé :** Vérification instantanée de 50 règles de sécurité critiques (Permissions, Services SSH, Configuration Réseau, Logging, Contrôle d'accès).
* **🛡️ Durcissement (Hardening) :** Remédiation automatisée des vulnérabilités en un clic via des playbooks Ansible idempotents.
* **↩️ Rollback Global :** Restauration immédiate des paramètres permissifs par défaut pour les démonstrations ou la reprise après erreur.
* **🤖 Mode Auto-Remédiation :** Boucle de surveillance en arrière-plan qui détecte et corrige automatiquement les dérives de configuration.
* **🔌 Déploiement "Plug & Play" (USB) :** Script d'installation autonome qui installe les dépendances manquantes silencieusement et lance un menu interactif.

## 🛠️ Architecture & Stack Technique

* **Backend API :** Python 3, FastAPI, Uvicorn
* **Orchestration & Sécurité :** Ansible (Playbooks YAML)
* **Frontend :** HTML5, Tailwind CSS, JavaScript (Vanilla)
* **Système / Scripts :** Bash, Whiptail (TUI), Linux Ubuntu

## 🚀 Installation & Utilisation

### Option 1 : Intervention Physique (Clé USB / TUI)
Idéal pour durcir un serveur "bare-metal" sans interface graphique.

1. Clonez ce dépôt à la racine d'une clé USB (formatée en `ext4` ou `exFAT`).
2. Branchez la clé sur le serveur cible.
3. Exécutez le lanceur avec les privilèges administrateur :
   ```bash
   sudo ./start_agent.sh
