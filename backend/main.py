import os
import subprocess
import re
import asyncio
from fastapi import FastAPI, Depends, HTTPException, Security, BackgroundTasks
from fastapi.security import APIKeyHeader
from fastapi.responses import FileResponse
from pydantic import BaseModel

os.environ["ANSIBLE_HOST_KEY_CHECKING"] = "False"
# 1. INITIALISATION DE L'APPLICATION
app = FastAPI(
    title="Plateforme de Hardening CIS",
    description="API centralisée pour l'audit et le durcissement",
    version="1.0.0"
)

# --- 2. CONFIGURATION DE LA SÉCURITÉ ---
API_KEY = "cis_secret_key_2026"
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Accès refusé : Clé API invalide")
    return api_key
# ------------------------------------

# --- 3. LOGIQUE D'AUTOMATISATION ---
AUTO_REMEDIATION_ACTIVE = False

def executer_audit_interne():
    cmd = [
        "ansible-playbook", 
        "-i", "ansible/inventory.ini", 
        "ansible/playbooks/audit_cis_global.yml",
        "--extra-vars", "ansible_become_pass=emsi"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    pattern = r"(\d+\.\s[^:]+):\s(NON CONFORME|CONFORME)"
    matches = re.findall(pattern, result.stdout)
    score = sum(1 for _, statut in matches if statut == "CONFORME")
    return score

async def boucle_surveillance_automatique():
    global AUTO_REMEDIATION_ACTIVE
    while AUTO_REMEDIATION_ACTIVE:
        print("[AUTO] Lancement de l'audit automatique...")
        score = executer_audit_interne()
        print(f"[AUTO] Score actuel : {score}/10")
        
        if score < 10:
            print("[AUTO] Écart détecté ! Lancement de la remédiation automatique...")
            cmd_harden = [
                "ansible-playbook", 
                "-i", "ansible/inventory.ini", 
                "ansible/playbooks/harden_cis_global.yml",
                "--extra-vars", "ansible_become_pass=emsi"
            ]
            subprocess.run(cmd_harden, capture_output=True, text=True)
            print("[AUTO] Remédiation terminée.")
            
        await asyncio.sleep(45)

# --- 4. MODÈLES DE DONNÉES ---
class ServeurModel(BaseModel):
    nom: str
    ip: str
    utilisateur: str = "root"
    password: str

# --- 5. ROUTES DE L'API ---

@app.get("/")
def lire_interface():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(os.path.dirname(current_dir), "frontend", "index.html")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Fichier introuvable : {file_path}")
    return FileResponse(file_path)

@app.post("/api/v1/auto/toggle", dependencies=[Depends(verify_api_key)])
def toggle_auto_mode(activer: bool, background_tasks: BackgroundTasks):
    global AUTO_REMEDIATION_ACTIVE
    AUTO_REMEDIATION_ACTIVE = activer
    if activer:
        background_tasks.add_task(boucle_surveillance_automatique)
    status_str = "activé" if activer else "désactivé"
    return {"message": f"Mode automatique {status_str} avec succès", "etat": AUTO_REMEDIATION_ACTIVE}

# --- GESTION DES SERVEURS (AJOUT, LECTURE, SUPPRESSION) ---

@app.get("/api/v1/servers", dependencies=[Depends(verify_api_key)])
def lister_serveurs():
    """Lit l'inventaire Ansible et retourne la liste des serveurs enregistrés."""
    inventory_path = "ansible/inventory.ini"
    serveurs_trouves = [{"nom": "localhost", "label": "localhost (Interne)"}]
    
    if os.path.exists(inventory_path):
        with open(inventory_path, "r") as f:
            for ligne in f:
                ligne = ligne.strip()
                if ligne and not ligne.startswith(("[", "#")) and "ansible_host=" in ligne:
                    nom_serveur = ligne.split()[0]
                    if nom_serveur != "localhost":
                        serveurs_trouves.append({"nom": nom_serveur, "label": nom_serveur})
                        
    return {"serveurs": serveurs_trouves}

@app.post("/api/v1/servers/add", dependencies=[Depends(verify_api_key)])
def ajouter_serveur(serveur: ServeurModel):
    inventory_path = "ansible/inventory.ini"
    nouvelle_ligne = (
        f"{serveur.nom} ansible_host={serveur.ip} "
        f"ansible_user={serveur.utilisateur} "
        f"ansible_password='{serveur.password}' "
        f"ansible_become_password='{serveur.password}'\n"
    )
    try:
        if not os.path.exists(inventory_path):
            with open(inventory_path, "w") as f:
                f.write("[serveurs_production]\n")
        with open(inventory_path, "a") as f:
            f.write(nouvelle_ligne)
        return {"message": f"Serveur '{serveur.nom}' ({serveur.ip}) ajouté avec succès !"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'écriture : {str(e)}")

@app.delete("/api/v1/servers/{nom_serveur}", dependencies=[Depends(verify_api_key)])
def supprimer_serveur(nom_serveur: str):
    """Supprime un serveur de l'inventaire Ansible."""
    if nom_serveur == "localhost":
        raise HTTPException(status_code=400, detail="Impossible de supprimer localhost")
        
    inventory_path = "ansible/inventory.ini"
    if not os.path.exists(inventory_path):
        raise HTTPException(status_code=404, detail="Inventaire introuvable")

    with open(inventory_path, "r") as f:
        lignes = f.readlines()

    with open(inventory_path, "w") as f:
        for ligne in lignes:
            if not ligne.startswith(nom_serveur + " "):
                f.write(ligne)
                
    return {"message": f"Serveur '{nom_serveur}' supprimé de l'inventaire."}

# --- ACTIONS ANSIBLE (AUDIT, HARDENING, ROLLBACK) ---
"""
@app.post("/api/v1/audit/global", dependencies=[Depends(verify_api_key)])
def run_global_audit(machine: str = "localhost"):
    cmd = [
        "ansible-playbook", 
        "-i", "ansible/inventory.ini", 
        "ansible/playbooks/audit_cis_global.yml",
        "--limit", machine,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    pattern = r"(\d+\.\s[^:]+):\s(NON CONFORME|CONFORME)"
    matches = re.findall(pattern, result.stdout)
    score_conforme = 0
    details_audit = []
    for regle, statut in matches:
        if statut == "CONFORME":
            score_conforme += 1
        details_audit.append({
            "controle": regle.strip(),
            "statut": statut
        })
    return {
        "titre": f"Rapport d'Audit - {machine}",
        "score": f"{score_conforme}/10",
        "taux_conformite": f"{(score_conforme / 10) * 100}%",
        "resultats": details_audit
    }
"""

@app.post("/api/v1/audit/global", dependencies=[Depends(verify_api_key)])
def run_global_audit(machine: str = "localhost"):
    cmd = [
        "ansible-playbook", 
        "-i", "ansible/inventory.ini", 
        "ansible/playbooks/audit_cis_global.yml",
        "--limit", machine,
	"--extra-vars", "ansible_become_flags='-H -S -p Password:'"
    ]
    
    # On lance la commande
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # --- DEBUG : Affichage des erreurs dans le terminal ---
    print(f"--- LOGS ANSIBLE POUR {machine} ---")
    if result.stderr:
        print("ERREUR :", result.stderr)
    print("SORTIE :", result.stdout)
    print("-----------------------------------")
    
    # Analyse des résultats
    pattern = r"(\d+\.\s[^:]+):\s(NON CONFORME|CONFORME)"
    matches = re.findall(pattern, result.stdout)
    
    score_conforme = 0
    details_audit = []
    
    for regle, statut in matches:
        if statut == "CONFORME":
            score_conforme += 1
        details_audit.append({
            "controle": regle.strip(),
            "statut": statut
        })
        
    return {
        "titre": f"Rapport d'Audit - {machine}",
        "score": f"{score_conforme}/10",
        "taux_conformite": f"{(score_conforme / 10) * 100}%",
        "resultats": details_audit
    }

@app.post("/api/v1/harden/global", dependencies=[Depends(verify_api_key)])
def run_global_hardening(machine: str = "localhost"):
    cmd = [
        "ansible-playbook", 
        "-i", "ansible/inventory.ini", 
        "ansible/playbooks/harden_cis_global.yml",
        "--limit", machine,
        "--extra-vars", "ansible_become_pass=emsi"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return {"message": f"Durcissement exécuté avec succès sur {machine}", "details": result.stdout}

@app.post("/api/v1/rollback/ssh", dependencies=[Depends(verify_api_key)])
def run_ssh_rollback(machine: str = "localhost"):
    cmd = [
        "ansible-playbook", 
        "-i", "ansible/inventory.ini", 
        "ansible/playbooks/rollback_ssh.yml",
        "--limit", machine,
        "--extra-vars", "ansible_become_pass=emsi"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return {"message": f"Rollback SSH exécuté sur {machine}", "details": result.stdout}
