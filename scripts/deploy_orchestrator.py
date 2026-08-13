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

def rebind_semantic_model(headers, prod_workspace_id, semantic_model_id, gold_lakehouse_id):
    """
    Religa o Semantic Model para apontar para o Lakehouse de PROD mantendo o Direct Lake.
    """
    print("\n   [Semantic Model] Aplicando Rebinding para Direct Lake (OneLake)...")
    
    # 1. Atualizar a Conexão
    bind_url = f"https://api.fabric.microsoft.com/v1/workspaces/{prod_workspace_id}/semanticModels/{semantic_model_id}/bindConnection"
    bind_payload = {
        "connectionBinding": {
            "connectivityType": "OneLake", 
            "connectionDetails": {
                "type": "Lakehouse",
                "path": f"{prod_workspace_id}/{gold_lakehouse_id}"
            }
        }
    }
    
    bind_response = requests.post(bind_url, headers=headers, json=bind_payload)
    
    if bind_response.status_code == 200:
        print("   [Semantic Model] Conexão atualizada com sucesso! Disparando Reframe...")
        
        # 2. Forçar a atualização dos metadados (Framing) dos arquivos Delta Parquet
        refresh_url = f"https://api.fabric.microsoft.com/v1/workspaces/{prod_workspace_id}/semanticModels/{semantic_model_id}/refreshes"
        refresh_payload = {"type": "Full"}
        requests.post(refresh_url, headers=headers, json=refresh_payload)
        
        print("   [Semantic Model] Reframe iniciado. O modelo está pronto para consumo!")
    else:
        print(f"    Erro ao atualizar conexão do Semantic Model: {bind_response.text}")

def main():
    if not CLIENT_ID:
        print(" Credenciais da SA não encontradas. O Deploy real foi pulado na POC.")
        return

    headers = get_fabric_headers()

    # ETAPA 1: ACIONAR O DEPLOYMENT PIPELINE
    print("\n Iniciando Deploy de DEV para PROD...")
    deploy_url = f"https://api.fabric.microsoft.com/v1/deploymentPipelines/{PIPELINE_ID}/deploy"
    deploy_payload = {
        "sourceStageId": "ID_ESTAGIO_DEV",  # <- Substitua depois pelo ID do estágio
        "targetStageId": "ID_ESTAGIO_PROD"  # <- Substitua depois pelo ID do estágio
    }
    
    deploy_response = requests.post(deploy_url, headers=headers, json=deploy_payload)
    print(f"Status do Deploy: {deploy_response.status_code}")
    
    # Dá um tempo para o Fabric criar os itens fisicamente no workspace de destino
    print("Aguardando 15 segundos para consolidação dos itens na nuvem...")
    time.sleep(15) 

    # ETAPA 2: MAPEAMENTO DE ESTADO
    print("\n🔍 Buscando os novos GUIDs em PROD...")
    items_url = f"https://api.fabric.microsoft.com/v1/workspaces/{PROD_WORKSPACE_ID}/items"
    items_response = requests.get(items_url, headers=headers)
    
    prod_guids = {}
    if items_response.status_code == 200:
        for item in items_response.json().get('value', []):
            prod_guids[item['displayName']] = item['id']
            print(f"   Encontrado: {item['displayName']} -> {item['id']}")
    
    # ETAPA 3: REBINDING 
    print("\n Executando Rebinding...")
    
    # Captura os IDs que o Fabric acabou de gerar em PROD
    sm_id = prod_guids.get('sm_cicd') # <- Coloque o nome real do modelo aqui
    lh_gold_id = prod_guids.get('lh_gold')
    
    if sm_id and lh_gold_id:
        rebind_semantic_model(headers, PROD_WORKSPACE_ID, sm_id, lh_gold_id)
    else:
        print("\n Não foi possível encontrar o Semantic Model ou o lh_gold em PROD. Verifique os nomes.")

    # (A lógica da Variable Library entraria aqui também, usando o mesmo princípio)

    print("\n Pipeline CI/CD concluído com sucesso!")

if __name__ == "__main__":
    main()
