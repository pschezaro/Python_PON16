import requests
import json
import time

# Configurações do Zendesk
SUBDOMINIO = "linktelwifi01"
EMAIL = "sysapi@linktelwifi.com/token"
TOKEN = "mNstaBe4NTjVNoLzLfQiiTZu7g5Clh8vdy19G1Pj"
HEADERS = {"Content-Type": "application/json"}

# URL da API do Zendesk
URL_TICKETS = f"https://{SUBDOMINIO}.zendesk.com/api/v2/tickets/create_many.json"
URL_SEARCH_USER = f"https://{SUBDOMINIO}.zendesk.com/api/v2/users/search.json?query="

# Dados comuns dos chamados
ASSUNTO = "Massiva - Instabilidade no serviço"
DESCRICAO = "Estamos cientes de uma instabilidade afetando o serviço e já estamos trabalhando para resolver."

# Campos personalizados do Zendesk (IDs precisam ser atualizados conforme sua conta)
ID_TELEFONE = 360039303732
ID_RECLAMANTE = 360039302832

# ID da organização "Prefeitura de Itapevi"
ORGANIZATION_ID = "361186918231"
GROUP_ID = "360012919412"

# Lista de clientes
clientes = [
    
    {"name": "CEMEB Jornalista Joao Valerio de Paula Neto"},
    {"name": "CRAS Amador Bueno"},
    {"name": "CEMEB Maria Jose Faria Biagione"},
    {"name": "Posto da Guarda Municipal - Amador Bueno"},
    {"name": "CEMEB Vereador Roberval Luiz Mendes da Silva"},
    {"name": "CEMEB Prof Alice Celestino Izabo Ramari"},
    {"name": "CEMEB Associacao Apecatu"},
    {"name": "CEMEB Evany Camargo Ribeiro"},
    {"name": "UBS Amador Bueno"},
    {"name": "ETI Padre Gerald Cluskey"},
    {"name": "CEMEB Prof Rosana Minani Andrade"},
    {"name": "Praca Paulo Franca Amador Bueno"},


]

# Função para buscar usuário no Zendesk dentro da organização
def buscar_usuario(nome_cliente):
    url = f"{URL_SEARCH_USER}{nome_cliente}"
    response = requests.get(url, headers=HEADERS, auth=(EMAIL, TOKEN))

    if response.status_code == 200:
        users = response.json().get("users", [])
        for user in users:
            if user.get("name") == nome_cliente and str(user.get("organization_id")) == ORGANIZATION_ID:
                print(f"✅ Usuário encontrado: {nome_cliente} (ID: {user.get('id')})")
                return user.get("id")  # Retorna o ID do usuário existente

    print(f"❌ Usuário não encontrado: {nome_cliente}")
    return None  # Retorna None se o usuário não for encontrado

# Criando tickets sem duplicar usuários
tickets_data = {"tickets": []}

for cliente in clientes:
    nome_cliente = cliente["name"]
    usuario_id = buscar_usuario(nome_cliente)

    ticket = {
        "subject": ASSUNTO,
        "comment": {"body": f"Olá {nome_cliente},\n\n{DESCRICAO}"},
        "organization_id": ORGANIZATION_ID,
        "group_id": GROUP_ID,
        "priority": "high",
        "status": "open",  # Define o status como "Aberto"
        "custom_fields": [
            {"id": ID_TELEFONE, "value": "1121977040"},
            {"id": ID_RECLAMANTE, "value": "Suporte"}
        ]
    }

    # Se o usuário já existe, usa o ID dele
    if usuario_id:
        ticket["requester_id"] = usuario_id
    else:
        ticket["requester"] = {"name": nome_cliente, "organization_id": ORGANIZATION_ID}  # Cria um novo usuário apenas se necessário

    tickets_data["tickets"].append(ticket)

# Enviar requisição para o Zendesk
response = requests.post(URL_TICKETS, headers=HEADERS, auth=(EMAIL, TOKEN), data=json.dumps(tickets_data))

# Verifica resposta e busca os IDs dos chamados criados
if response.status_code in [200, 201]:
    response_data = response.json()
    job_status = response_data.get("job_status", {})
    job_id = job_status.get("id")

    print(f"✅ Chamados enviados com sucesso! ID do job: {job_id}")
    print("🔄 Aguardando criação dos chamados...")

    # URL para verificar o status do job
    job_url = f"https://{SUBDOMINIO}.zendesk.com/api/v2/job_statuses/{job_id}.json"

    while True:
        job_response = requests.get(job_url, headers=HEADERS, auth=(EMAIL, TOKEN))
        job_data = job_response.json()
        status = job_data.get("job_status", {}).get("status")

        if status == "completed":
            results = job_data.get("job_status", {}).get("results", [])

            if results and "id" in results[0]:
                ticket_ids = [result["id"] for result in results]
                print("🎫 Chamados criados com sucesso!")
                for i, ticket_id in enumerate(ticket_ids):
                    print(f"📌 Cliente: {clientes[i]['name']} → Ticket ID: {ticket_id} (Status: Aberto)")
            else:
                print("❌ Nenhum ID de ticket encontrado na resposta. Verifique a estrutura do retorno.")

            break
        elif status == "failed":
            print("❌ Falha ao criar alguns chamados.")
            break

        time.sleep(2)  # Aguarda 2 segundos antes de consultar novamente

else:
    print(f"❌ Erro ao criar tickets: {response.status_code}")
    print(response.text)
