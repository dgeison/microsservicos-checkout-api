from fastapi import APIRouter

from app.checkout.checkout_process import checkout_process

# APIRouter agrupa as rotas do checkout separadas do main.py.
# prefix="/checkout" significa que todas as rotas aqui começam com /checkout.
# tags=["Checkout"] agrupa os endpoints na documentação automática do FastAPI (http://localhost:8000/docs).
router = APIRouter(prefix="/checkout", tags=["Checkout"])

# Registra o endpoint POST /checkout/process apontando para a função checkout_process.
# Equivalente a escrever @router.post("/process") em cima da função.
router.add_api_route("/process", endpoint=checkout_process, methods=["POST"])
