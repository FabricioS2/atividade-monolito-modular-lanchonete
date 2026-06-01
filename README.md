# Monólito Modular - Sistema de Lanchonete

## Integrantes

Alan David, Pablo Murillo e Fabricio Guilherme

---

# Arquitetura

O sistema foi desenvolvido utilizando o padrão Monólito Modular.

A aplicação foi dividida em módulos independentes:

- Cardápio
- Pedidos
- Pagamento
- Notificação

Cada módulo possui sua própria camada de serviço e comunicação através de APIs internas.

Estrutura:

```text
core/
├── cardapio/
├── pedidos/
├── pagamento/
├── notificacao/
├── api/
├── models.py
├── admin.py
└── urls.py
```

---

# Comunicação entre módulos

Os módulos não acessam diretamente os repositórios uns dos outros.

Exemplo:

PagamentoService
→ PedidoAPI
→ NotificacaoAPI

Essa abordagem reduz o acoplamento e facilita uma futura migração para microsserviços.

---

# Schemas do Banco

O banco PostgreSQL foi organizado em schemas separados.

## cardapio

- item

## pedidos

- pedido
- item_pedido

## pagamento

- forma_pagamento
- transacao_mock

## notificacao

- notificacao_cozinha

---

# Como executar

## Clonar o projeto

```bash
git clone <repositorio>
```

## Ativar ambiente virtual

Windows

```bash
.venv\Scripts\activate
```

## Instalar dependências

```bash
pip install -r requirements.txt
```

## Executar migrations

```bash
python manage.py migrate
```

## Criar superusuário

```bash
python manage.py createsuperuser
```

## Executar servidor

```bash
python manage.py runserver
```

---

# Como testar

## Health Check

GET

```http
/api/health/
```

Resposta:

```json
{
  "status": "UP",
  "application": "monolito-modular-lanchonete"
}
```

---

## Criar Item

POST

```http
/api/itens/
```

Exemplo:

```json
{
  "nome": "Hambúrguer",
  "preco": 15.00,
  "descricao": "Hambúrguer artesanal",
  "quantidade_estoque": 50,
  "disponivel": true
}
```

---

## Criar Pedido

POST

```http
/api/pedidos/
```

Exemplo:

```json
{
  "itens": [
    {
      "item": 1,
      "quantidade": 2
    }
  ]
}
```

---

## Efetuar Pagamento

POST

```http
/api/pedidos/1/pagar/
```

Exemplo:

```json
{
  "forma_pagamento_id": 1
}
```

---

## Consultar Notificações

GET

```http
/api/notificacoes/
```

---

# Experimento Obrigatório

Foi realizada a troca da implementação do gateway de pagamento.

Implementação original:

- MockGateway

Nova implementação:

- PixGateway

A alteração ocorreu apenas dentro do módulo de pagamento.

Nenhum outro módulo precisou ser modificado.

