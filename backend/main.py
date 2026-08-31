import os
import subprocess
import re
import asyncio
from fastapi import FastAPI, Depends, HTTPException, Security, BackgroundTasks
from fastapi.security import APIKeyHeader
from fastapi.responses import FileResponse

os.environ["ANSIBLE_HOST_KEY_CHECKING"] = "False"

# 1. INITIALISATION DE L'APPLICATION
app = FastAPI(
    title="Agent de Hardening CIS - Local",
    description="API de l'agent local pour l'audit et le durcissement du système hôte",
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
        "--limit", "localhost"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    pattern = r"((?:\d+\.)?\d+\.\s[^:]+):\s(NON CONFORME|CONFORME)"
    matches = re.findall(pattern, result.stdout)
    score = sum(1 for _, statut in matches if statut == "CONFORME")
    total_regles = len(matches)
    return score, total_regles

async def boucle_surveillance_automatique():
    global AUTO_REMEDIATION_ACTIVE
    while AUTO_REMEDIATION_ACTIVE:
        print("[AUTO] Lancement de l'audit automatique local...")
        score, total = executer_audit_interne()
        print(f"[AUTO] Score actuel : {score}/{total}")
        
        # Si le score n'est pas parfait, on durcit
        if score < total and total > 0:
            print("[AUTO] Écart détecté ! Lancement de la remédiation automatique...")
            cmd_harden = [
                "ansible-playbook", 
                "-i", "ansible/inventory.ini", 
                "ansible/playbooks/harden_cis_global.yml",
                "--limit", "localhost"
            ]
            subprocess.run(cmd_harden, capture_output=True, text=True)
            print("[AUTO] Remédiation terminée.")
            
        await asyncio.sleep(45)

# --- 4. ROUTES DE L'INTERFACE ---

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

# --- 5. ACTIONS ANSIBLE LOCALES (AUDIT, HARDENING, ROLLBACK) ---

@app.post("/api/v1/audit/global", dependencies=[Depends(verify_api_key)])
def run_global_audit(machine: str = "localhost"):
    cmd = [
        "ansible-playbook", 
        "-i", "ansible/inventory.ini", 
        "ansible/playbooks/audit_cis_global.yml",
        "--limit", machine
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Regex dynamique
    pattern = r"((?:\d+\.)?\d+\.\s[^:]+):\s(NON CONFORME|CONFORME)"
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
    
    # Protection anti-division par zéro
    total_regles = len(matches) if len(matches) > 0 else 1
    taux = (score_conforme / total_regles) * 100
        
    return {
        "titre": f"Rapport d'Audit Local",
        "score": f"{score_conforme}/{len(matches)}",
        "taux_conformite": f"{taux:.2f}%", 
        "resultats": details_audit
    }

@app.post("/api/v1/harden/global", dependencies=[Depends(verify_api_key)])
def run_global_hardening(machine: str = "localhost"):
    cmd = [
        "ansible-playbook", 
        "-i", "ansible/inventory.ini", 
        "ansible/playbooks/harden_cis_global.yml",
        "--limit", machine
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return {"message": f"Durcissement exécuté avec succès sur le système local", "details": result.stdout}

@app.post("/api/v1/rollback/global", dependencies=[Depends(verify_api_key)])
def run_global_rollback(machine: str = "localhost"):
    cmd = [
        "ansible-playbook", 
        "-i", "ansible/inventory.ini", 
        "ansible/playbooks/rollback_cis_global.yml",
        "--limit", machine
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return {"message": f"Restauration exécutée avec succès sur le système local", "details": result.stdout}
