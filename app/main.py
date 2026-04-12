import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager

from app.client_manager import client_manager
from app.checkout.router import router as checkout_router
from app.infra.dabase import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    # Startup: Create database tables
    await create_tables()
    await client_manager.startup()
    yield
    await client_manager.shutdown()


load_dotenv()

# Instância principal da aplicação FastAPI
app = FastAPI(title="Checkout Commerce API", version="1.0.0", lifespan=lifespan)

app.include_router(checkout_router)


# @app.get("/health") é um decorator: registra a função abaixo como handler do endpoint GET /health.
# Quando alguém chamar GET http://localhost:8000/health, o FastAPI executa health_check() e devolve o resultado.
@app.get("/health")
async def health_check():
    # Padrão de health check: resposta simples que confirma que a aplicação está viva e respondendo.
    # Ferramentas de monitoramento, Docker e orquestradores (ex: Kubernetes) consultam este endpoint
    # para saber se o serviço está saudável antes de rotear tráfego para ele.
    return {"status": "healthy"}


@app.get("/payment")
async def payment_process():
    # Função de exemplo para processar o pagamento. Em produção, aqui seriam feitas chamadas reais
    # para o microsserviço de pagamento (payment-service) usando HTTP ou gRPC.
    payment_url = os.getenv("PAYMENT_SERVICE_URL")
    return {"payment_status": payment_url}


if __name__ == "__main__":
    import uvicorn

    # Executa o servidor Uvicorn para servir a aplicação FastAPI.
    # host="0.0.0.0" permite que o servidor aceite conexões de qualquer endereço IP.
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8085))
    uvicorn.run(app, host=host, port=port)
