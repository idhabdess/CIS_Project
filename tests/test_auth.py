from fastapi.testclient import TestClient
from backend.main import app

# Création du client de test qui simule le navigateur/frontend
client = TestClient(app)

def test_audit_without_api_key():
    """Test 1: Requête sans aucune clé API (doit être rejetée)"""
    response = client.post("/api/v1/audit/global")
    assert response.status_code == 401  # FastAPI renvoie 403 par défaut si le header manque

def test_audit_with_invalid_api_key():
    """Test 2: Requête avec une mauvaise clé API (doit être rejetée)"""
    response = client.post(
        "/api/v1/audit/global", 
        headers={"X-API-Key": "hacker_key_123"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Accès refusé : Clé API invalide"}
