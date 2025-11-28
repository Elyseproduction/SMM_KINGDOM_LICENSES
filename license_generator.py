import requests
import base64
import datetime
import uuid
import os
import sys

# --- CONFIGURATION SÉCURISÉE DE GITHUB (À REMPLACER) ---
# 1. Personal Access Token (PAT) avec la permission 'repo'
GITHUB_TOKEN = "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" 
# 2. Votre nom d'utilisateur GitHub
GITHUB_OWNER = "Elyseproduction" 
# 3. Nom du dépôt où les licences seront stockées (ex: SMM_KINGDOM_LICENSES)
GITHUB_REPO = "SMM_KINGDOM_LICENSES" 
# 4. Nom du fichier de base de données des licences
LICENSE_FILENAME = "active_licenses.json" 

# --- COULEURS ET FORMATAGE ---
R = '\033[0m'
VERT = '\033[32m'
ROUGE = '\033[31m'
JAUNE = '\033[33m'
GRAS = '\033[1m'

# --- LOGIQUE DE GÉNÉRATION ET GITHUB ---

def generate_license_code(prefix="SMM"):
    """
    Génère un code license unique et structuré.
    Format: [PREFIX]-[YMD]-[UUID_PART]
    """
    # UUID pour l'unicité
    unique_id_part = uuid.uuid4().hex.upper()[:10]
    # Date pour le suivi
    timestamp = datetime.datetime.now().strftime("%y%m%d")
    
    # Code final : SMM-251128-ABCDEF1234
    license_code = f"{prefix}-{timestamp}-{unique_id_part}"
    return license_code


def get_current_file_data():
    """
    Récupère le SHA actuel du fichier et son contenu.
    Ceci est nécessaire pour mettre à jour un fichier sur GitHub (API PUT).
    """
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{LICENSE_FILENAME}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        # Fichier existe : retourne le SHA et le contenu décodé
        content_b64 = response.json()['content']
        sha = response.json()['sha']
        current_content = base64.b64decode(content_b64).decode('utf-8')
        return sha, current_content
    elif response.status_code == 404:
        # Fichier n'existe pas : c'est une création
        return None, None
    else:
        print(f"{ROUGE}Erreur GitHub lors de la récupération : {response.status_code}. Vérifiez les tokens.{R}")
        print(f"{response.json().get('message', 'Détails non disponibles')}")
        sys.exit(1)


def update_github_file(new_content_str, sha, license_code):
    """
    Met à jour (ou crée) le fichier de licences sur GitHub.
    """
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{LICENSE_FILENAME}"
    
    # Le contenu doit être encodé en base64
    content_encoded = base64.b64encode(new_content_str.encode('utf-8')).decode('utf-8')
    
    commit_message = f"🤖 Bot Telegram: Ajout de la nouvelle licence {license_code}"
    
    data = {
        "message": commit_message,
        "content": content_encoded,
        "sha": sha if sha else None # SHA est requis si le fichier existe
    }

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Utilisation de PUT pour créer/mettre à jour
    response = requests.put(url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        return True, response.json()['content']['html_url']
    else:
        print(f"{ROUGE}Erreur lors du dépôt GitHub ({response.status_code}): {response.json().get('message', 'Inconnu')}{R}")
        return False, None


def generate_and_upload_license(username_or_user_id):
    """
    Fonction principale appelée par le Bot Telegram.
    Génère la licence, met à jour le JSON et le dépose sur GitHub.
    """
    if GITHUB_TOKEN == "<VOTRE_PERSONAL_ACCESS_TOKEN_GITHUB>":
        print(f"{ROUGE}{GRAS}ERREUR DE CONFIGURATION : Veuillez remplacer les placeholders dans le script.{R}")
        return None
        
    license_code = generate_license_code()
    
    # 1. Récupérer l'état actuel du fichier sur GitHub
    sha, current_content_str = get_current_file_data()

    # 2. Préparer les données pour la mise à jour
    new_entry = {
        "code": license_code,
        "generated_for": username_or_user_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "status": "ACTIVE"
    }
    
    if current_content_str:
        # Le fichier existe: On charge le JSON existant
        try:
            licenses_list = json.loads(current_content_str)
        except json.JSONDecodeError:
            # Si le fichier est corrompu, on repart d'une liste vide
            licenses_list = []
            
        licenses_list.append(new_entry)
    else:
        # Le fichier n'existe pas: On crée la première entrée
        licenses_list = [new_entry]
    
    # Convertir la liste mise à jour en chaîne JSON formatée
    new_content_str = json.dumps(licenses_list, indent=4)
    
    # 3. Mettre à jour le fichier sur GitHub
    success, url = update_github_file(new_content_str, sha, license_code)

    if success:
        print(f"{VERT}{GRAS}✅ Succès : Le code license {license_code} a été enregistré sur GitHub.{R}")
        print(f"{VERT}URL du commit : {url.replace('blob', 'commit').split('?ref=main')[0]}{R}")
        return license_code
    else:
        print(f"{ROUGE}{GRAS}❌ Échec de l'enregistrement sur GitHub. Veuillez vérifier la console pour les erreurs.{R}")
        return None


if __name__ == "__main__":
    # --- Exemple d'utilisation (Simule l'appel du bot) ---
    print(JAUNE + GRAS + "="*50 + R)
    print(BLANC + GRAS + " SIMULATION DE GÉNÉRATION DE LICENCE" + R)
    print(JAUNE + GRAS + "="*50 + R)

    # Simule l'ID Telegram de l'utilisateur demandeur
    TEST_USER_ID = "telegram_user_45678" 

    generated_code = generate_and_upload_license(TEST_USER_ID)
    
    if generated_code:
        print(f"\n{VERT}Code généré pour l'utilisateur {TEST_USER_ID} : {GRAS}{generated_code}{R}")
        
    print(JAUNE + GRAS + "="*50 + R)
