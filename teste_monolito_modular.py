"""
Requisitos:
- Servidor Django rodando (ex.: python manage.py runserver)
- Usuário de teste já criado (configurar USER_EMAIL e USER_PASSWORD)
- Formas de pagamento ativas no banco (CREDIT_CARD, PIX, BOLETO)
- Biblioteca 'requests' instalada
"""

import json
import sys
import requests
from requests.auth import HTTPBasicAuth

# ---------- CONFIGURAÇÕES ----------
BASE_URL = "http://127.0.0.1:8000/api"
USER_EMAIL = "teste@teste.com"
USER_PASSWORD = "teste123"

# ---------- FUNÇÕES AUXILIARES ----------
def autenticar():
    return HTTPBasicAuth(USER_EMAIL, USER_PASSWORD)

def chamar_api(metodo, url, **kwargs):
    """
    Executa uma requisição HTTP e imprime detalhes da requisição e resposta.
    """
    auth = kwargs.pop('auth', None)
    json_data = kwargs.pop('json', None)
    headers = kwargs.pop('headers', {})

    print(f"\n📤 REQUISIÇÃO {metodo.upper()} {url}")
    if auth:
        print(f"   Auth: Basic {USER_EMAIL}:****")
    if headers:
        print(f"   Headers: {headers}")
    if json_data:
        print(f"   Body (JSON): {json.dumps(json_data, indent=2, ensure_ascii=False)}")

    resposta = requests.request(
        method=metodo,
        url=url,
        auth=auth,
        json=json_data,
        headers=headers,
        **kwargs
    )

    print(f"📥 RESPOSTA {resposta.status_code}")
    try:
        corpo = resposta.json()
        print(f"   Body: {json.dumps(corpo, indent=2, ensure_ascii=False)}")
    except ValueError:
        conteudo = resposta.text[:300].replace('\n', ' ')
        print(f"   Body: (não-JSON) {conteudo}")

    return resposta

def tratar_resposta(resp, esperado=200):
    if resp.status_code != esperado:
        print(f"  ⚠️ Status inesperado: {resp.status_code} (esperado {esperado})")
        return False
    return True

def verificar_precondicoes():
    """
    Antes de rodar os testes, verifica se o usuário consegue autenticar
    e se existem formas de pagamento ativas.
    """
    print("🔍 Verificando precondições...")
    auth = autenticar()

    # Testa autenticação (qualquer endpoint protegido serve)
    r = chamar_api('get', f"{BASE_URL}/pedidos/", auth=auth)
    if r.status_code == 401 or r.status_code == 403:
        print(f"❌ Falha na autenticação com {USER_EMAIL}. Verifique as credenciais.")
        sys.exit(1)
    elif r.status_code != 200:
        print(f"⚠️ Resposta inesperada ao testar autenticação (status {r.status_code}). Continuando mesmo assim...")
    else:
        print("✅ Autenticação OK")

    # Verifica formas de pagamento
    r = chamar_api('get', f"{BASE_URL}/formas-pagamento/")
    if r.status_code == 200:
        formas = r.json()
        if not formas:
            print("❌ Nenhuma forma de pagamento ativa. Crie ao menos uma no Django Admin.")
            sys.exit(1)
        print(f"✅ Formas de pagamento ativas: {[f['nome'] for f in formas]}")
    else:
        print(f"❌ Não foi possível obter formas de pagamento (status {r.status_code}).")
        sys.exit(1)

def primeira_forma_pagamento_id():
    """Retorna o ID da primeira forma de pagamento ativa."""
    r = chamar_api('get', f"{BASE_URL}/formas-pagamento/")
    formas = r.json()
    return formas[0]['id'] if formas else None

def deletar_item_seguro(item_id, auth):
    """Tenta deletar um item; se falhar por proteção, exibe aviso."""
    r = chamar_api('delete', f"{BASE_URL}/itens/{item_id}/", auth=auth)
    if r.status_code == 204:
        print("  ✅ Item deletado com sucesso.")
    else:
        print(f"  ⚠️ Não foi possível deletar o item {item_id} (protegido por pedidos existentes).")
        if r.status_code == 500:
            print("     (Provavelmente ProtectedError: item vinculado a ItemPedido)")

# ---------- TESTES ----------
def test_health():
    print("\n🔍 Testando health check...")
    r = chamar_api('get', f"{BASE_URL}/health/")
    if tratar_resposta(r, 200):
        assert r.json()["status"] == "UP"
        print("  ✅ Health OK")

def test_crud_itens():
    print("\n🔍 Testando CRUD de Itens...")
    auth = autenticar()

    # Criar
    novo_item = {
        "nome": "Pastel de Teste",
        "preco": "9.99",
        "descricao": "Pastel crocante de teste",
        "quantidade_estoque": 10,
        "disponivel": True
    }
    r = chamar_api('post', f"{BASE_URL}/itens/", json=novo_item, auth=auth)
    if not tratar_resposta(r, 201):
        return
    item_id = r.json()["id"]
    print(f"  ✅ Item criado (id={item_id})")

    # Listar
    r = chamar_api('get', f"{BASE_URL}/itens/")
    if tratar_resposta(r, 200):
        print(f"  ✅ Listagem de itens: {len(r.json())} registros")

    # Recuperar
    r = chamar_api('get', f"{BASE_URL}/itens/{item_id}/")
    if tratar_resposta(r, 200):
        print(f"  ✅ Item recuperado: {r.json()['nome']}")

    # Atualizar
    atualizacao = {
        "nome": "Pastel Atualizado",
        "preco": "11.50",
        "descricao": "Nova descrição",
        "quantidade_estoque": 5,
        "disponivel": False
    }
    r = chamar_api('put', f"{BASE_URL}/itens/{item_id}/", json=atualizacao, auth=auth)
    if tratar_resposta(r, 200):
        print(f"  ✅ Item atualizado: {r.json()['nome']}")

    # Deletar
    deletar_item_seguro(item_id, auth)

def test_formas_pagamento():
    print("\n🔍 Testando listagem de formas de pagamento...")
    r = chamar_api('get', f"{BASE_URL}/formas-pagamento/")
    if tratar_resposta(r, 200):
        dados = r.json()
        print(f"  ✅ {len(dados)} formas disponíveis: {[f['nome'] for f in dados]}")

def test_fluxo_pedido():
    print("\n🔍 Testando fluxo de pedido (criação, pagamento e notificação)...")
    auth = autenticar()

    # Criar item temporário
    item = {
        "nome": "Coxinha Teste",
        "preco": "5.00",
        "descricao": "Coxinha de frango",
        "quantidade_estoque": 20,
        "disponivel": True
    }
    r = chamar_api('post', f"{BASE_URL}/itens/", json=item, auth=auth)
    if not tratar_resposta(r, 201):
        return
    item_id = r.json()["id"]

    # Criar pedido
    pedido_data = {
        "itens": [
            {"item": item_id, "quantidade": 2}
        ]
    }
    r = chamar_api('post', f"{BASE_URL}/pedidos/", json=pedido_data, auth=auth)
    if not tratar_resposta(r, 201):
        deletar_item_seguro(item_id, auth)
        return
    pedido = r.json()
    pedido_id = pedido["id"]
    total = pedido["total"]
    print(f"  ✅ Pedido criado (id={pedido_id}, total={total})")

    # Listar pedidos
    r = chamar_api('get', f"{BASE_URL}/pedidos/", auth=auth)
    if tratar_resposta(r, 200):
        print(f"  ✅ Listagem de pedidos: {len(r.json())} encontrados")

    # Detalhar pedido
    r = chamar_api('get', f"{BASE_URL}/pedidos/{pedido_id}/", auth=auth)
    if tratar_resposta(r, 200):
        print(f"  ✅ Status do pedido: {r.json()['status']}")

    # Pagar pedido
    forma_id = primeira_forma_pagamento_id()
    if not forma_id:
        print("  ❌ Nenhuma forma de pagamento ativa!")
        deletar_item_seguro(item_id, auth)
        return

    r = chamar_api(
        'post',
        f"{BASE_URL}/pedidos/{pedido_id}/pagar/",
        json={"forma_pagamento_id": forma_id},
        auth=auth
    )
    if tratar_resposta(r, 200):
        print(f"  ✅ Pagamento: {r.json()['mensagem']}")
    else:
        print("  ⚠️ Falha no pagamento (status pode não ser 'CRIADO')")

    # Notificações
    print("\n🔍 Testando notificações da cozinha...")
    r = chamar_api('get', f"{BASE_URL}/notificacoes/", auth=auth)
    if tratar_resposta(r, 200):
        notificacoes = r.json()
        print(f"  ✅ Notificações: {len(notificacoes)}")
        if notificacoes:
            notif_id = notificacoes[0]["id"]
            r = chamar_api('post', f"{BASE_URL}/notificacoes/{notif_id}/marcar_lida/", auth=auth)
            if tratar_resposta(r, 200):
                print("  ✅ Marcada como lida")

    # Limpar item (provavelmente falhará por proteção)
    deletar_item_seguro(item_id, auth)

# ---------- EXECUÇÃO ----------
if __name__ == "__main__":
    print("🚀 Iniciando testes da API (modo independente de Django)...")
    verificar_precondicoes()

    try:
        test_health()
        test_crud_itens()
        test_formas_pagamento()
        test_fluxo_pedido()
        print("\n✅ Todos os testes executados.")
    except requests.exceptions.ConnectionError:
        print("\n❌ Erro de conexão. Verifique se o servidor está rodando em", BASE_URL)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")