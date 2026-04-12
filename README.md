# Checkout Commerce API

Estudo de microsserviços com **FastAPI**, **WireMock** e **Docker**.  
O projeto simula o fluxo completo de um checkout de e-commerce, orquestrando serviços de pagamento, estoque e pedido.

---

## Como nasceu este projeto

Um e-commerce tem várias partes: o **Site** e o **Mobile** onde o cliente navega e monta o **Carrinho de Compras**. Ao finalizar a compra, o carrinho dispara o **Checkout** — que é o coração do sistema. O Checkout não faz tudo sozinho: ele orquestra três microsserviços independentes, cada um com sua responsabilidade.

```mermaid
flowchart TD
    Site["🌐 Site"]
    Mobile["📱 Mobile"]
    Carrinho["🛒 Carrinho de Compras"]
    Checkout["🐍 Checkout\nFastAPI — porta 8085"]
    DB[("💾 PostgreSQL\nporta 5442\n→ registra status de cada etapa")]
    Payment["💳 Payment\nporta 8081\n→ cobra o cartão"]
    Inventory["📦 Inventory\nporta 8082\n→ baixa o estoque"]
    Order["📋 Order\nporta 8083\n→ cria o pedido"]

    Site --> Carrinho
    Mobile --> Carrinho
    Carrinho -->|"finaliza compra"| Checkout
    Checkout -->|"salva estado"| DB
    Checkout -->|"1º"| Payment
    Checkout -->|"2º"| Inventory
    Checkout -->|"3º"| Order
```

> O diagrama completo com arquitetura e sequência de chamadas está em [`architecture.drawio`](architecture.drawio).  
> Abra com a extensão **Draw.io Integration** no VS Code ou em [app.diagrams.net](https://app.diagrams.net).

---

## Ciclo de vida do Checkout

Cada etapa é persistida no banco — se algo falhar, sabemos exatamente onde parou:

```
PENDING → chama Payment → chama Inventory → chama Order → SUCCESS
                                                         ↘ FAILED (em qualquer etapa)
```

A cada falha o status é atualizado para `FAILED` e o motivo é salvo no banco antes de retornar.

---

## Stack

| Tecnologia | Papel |
|---|---|
| **FastAPI** | Framework web — recebe e roteia as requisições HTTP |
| **httpx** | Cliente HTTP assíncrono — faz as chamadas reais aos microsserviços |
| **Pydantic** | Valida os dados automaticamente (campo inválido = erro 422) |
| **SQLAlchemy + asyncpg** | ORM assíncrono para persistência no PostgreSQL |
| **WireMock** | Simula os microsserviços externos durante o desenvolvimento |
| **PostgreSQL** | Banco de dados relacional — persiste o estado de cada checkout |
| **Docker** | Sobe o PostgreSQL e os serviços WireMock de forma isolada e reproduzível |
| **uv** | Gerenciador de dependências Python |

---

## Estrutura do projeto

```
app/
├── main.py                   # Ponto de entrada — lifespan cria as tabelas na startup
├── client_manager.py         # Gerencia o ciclo de vida dos clientes HTTP (startup/shutdown)
├── checkout/
│   ├── router.py             # Rotas do checkout (POST /checkout/process)
│   ├── checkout_process.py   # Orquestra as chamadas aos microsserviços
│   ├── checkout_request.py   # Modelos de entrada (Pydantic)
│   └── checkout_model.py     # Modelo do banco (SQLAlchemy) + enum de status
└── infra/
    ├── dabase.py             # Engine async, sessão e create_tables()
    └── client/
        ├── payment_client.py   # HTTP client → Payment service (porta 8081) com retry
        ├── inventory_client.py # HTTP client → Inventory service (porta 8082)
        └── order_client.py     # HTTP client → Order service (porta 8083)

wiremock/
├── payment/mappings/         # Mock do serviço de pagamento (porta 8081)
├── inventory/mappings/       # Mock do serviço de estoque (porta 8082)
└── order/mappings/           # Mock do serviço de pedidos (porta 8083)
```

---

## Como rodar

### 1. Suba o PostgreSQL e os serviços WireMock

```bash
docker compose up -d
```

> O PostgreSQL sobe na porta `5442` e o banco `checkout_db` é criado automaticamente.  
> As tabelas são criadas pela própria aplicação na startup (via `lifespan`).

### 2. Configure o ambiente

```bash
cp .env.example .env
# edite o .env com suas configurações
```

### 3. Instale as dependências

```bash
uv sync
```

### 4. Suba a API

```bash
uv run python app/main.py
```

A API estará disponível em `http://localhost:8085`.  
Documentação automática: `http://localhost:8085/docs`

---

## Testando os endpoints

Use o arquivo [`request.http`](request.http) com a extensão **REST Client** do VS Code ou execute via curl:

```bash
# Health check
curl http://localhost:8085/health

# Processar checkout
curl -X POST http://localhost:8081/payments/process \
  -H "Content-Type: application/json" \
  -d '{"amount": 1000.01, "currency": "BRL"}'
```

---

## Resiliência — tratamento de falhas

Cada client HTTP (`payment_client`, `inventory_client`, `order_client`) captura erros em camadas:

| Exceção | Causa | Mensagem retornada |
|---|---|---|
| `ConnectError` | Serviço fora do ar / porta errada | `"... service unavailable"` |
| `TimeoutException` | Serviço lento ou travado | `"... service timeout"` |
| `HTTPStatusError` | Serviço respondeu com 4xx/5xx | corpo da resposta HTTP |
| `Exception` | Qualquer outro erro inesperado | mensagem da exceção |

Em qualquer falha o `checkout_process.py`:
1. Atualiza o status para `FAILED` no banco
2. Persiste a mensagem de erro
3. Retorna `HTTP 422` com `checkout_id`, tipo do erro e mensagem detalhada

### Retry com Exponential Backoff (Payment)

O `payment_client.py` tenta até **3 vezes** antes de desistir, com espera exponencial entre as tentativas:

```
Tentativa 1 → falha → aguarda 1s
Tentativa 2 → falha → aguarda 2s
Tentativa 3 → falha → retorna erro
```

> Erros 4xx (ex: cartão inválido) **não** são re-tentados — o problema está nos dados, não no serviço.

---

## Por que cada peça existe?

| Componente | Por que existe |
|---|---|
| **router.py** | Separa as rotas do `main.py` — cada módulo cuida das suas próprias rotas |
| **checkout_process.py** | Orquestra a lógica: chama pagamento, estoque e pedido na ordem certa |
| **checkout_model.py** | Representa o Checkout no banco — registra status e onde falhou |
| **lifespan (main.py)** | Evento de startup do FastAPI — garante que as tabelas existem antes de receber requisições |
| **create_tables (dabase.py)** | Cria as tabelas via SQLAlchemy sem precisar rodar migrations manualmente |
| **payment/inventory/order_client.py** | Clientes HTTP que chamam cada microsserviço; injetados via `Depends` do FastAPI |
| **client_manager.py** | Cria os `httpx.AsyncClient` uma única vez no startup e fecha no shutdown — evita abrir conexão por requisição |
| **WireMock** | Permite desenvolver sem depender de sistemas externos reais |
| **Docker** | Garante que o banco e os mocks rodam igual em qualquer máquina |
