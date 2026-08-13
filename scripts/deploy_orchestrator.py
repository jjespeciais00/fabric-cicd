import os
import time
import requests
from azure.identity import ClientSecretCredential

# 1. CARREGAR VARIÁVEIS DE AMBIENTE (Injetadas pelo GitHub Actions)
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
PROD_WORKSPACE_ID = os.getenv("PROD_WORKSPACE_ID")
PIPELINE_ID = os.getenv("PIPELINE_ID")

def get_fabric_headers():
    print("Autenticando via Service Principal...")
    credential = ClientSecretCredential(
        tenant_id=TENANT_ID,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )
    token = credential.get_token("https://api.fabric.microsoft.com/.default")
    return {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json"
    }

def main():
    # Validação de segurança para a POC
    if not CLIENT_ID:
        print("Credenciais da SA não encontradas. O Deploy real foi pulado na POC.")
        return

    headers = get_fabric_headers()

    # ETAPA 1: ACIONAR O DEPLOYMENT PIPELINE
    print("\n Iniciando Deploy de DEV para PROD...")
    deploy_url = f"https://api.fabric.microsoft.com/v1/deploymentPipelines/{PIPELINE_ID}/deploy"
    deploy_payload = {
        "sourceStageId": "ID_ESTAGIO_DEV",
        "targetStageId": "ID_ESTAGIO_PROD"
    }
    response = requests.post(deploy_url, headers=headers, json=deploy_payload)
    print(f"Status do Deploy: {response.status_code}")
    
    time.sleep(15) 

    # ETAPA 2: MAPEAMENTO DE ESTADO
    print("\n Buscando os novos GUIDs em PROD...")
    items_url = f"https://api.fabric.microsoft.com/v1/workspaces/{PROD_WORKSPACE_ID}/items"
    items_response = requests.get(items_url, headers=headers)
    
    prod_guids = {}
    if items_response.status_code == 200:
        for item in items_response.json().get('value', []):
            prod_guids[item['displayName']] = item['id']
            print(f"Encontrado em PROD: {item['displayName']} -> {item['id']}")
    
    # ETAPA 3: REBINDING
    print("\n Executando Rebinding da Variable Library e do Semantic Model...")
    # (A lógica detalhada de API de rebinding entrará aqui depois)

    print("\n Pipeline CI/CD concluído com sucesso!")

if __name__ == "__main__":
    main()
