from pydantic import BaseModel

# BaseModel do Pydantic garante que os dados recebidos na requisição
# tenham os tipos e campos corretos. Se algo estiver errado, retorna erro 422 automaticamente.


class PaymentMethodRequest(BaseModel):
    # Dados do cartão de pagamento enviados pelo cliente
    type: str  # ex: "credit_card", "debit_card"
    card_number: str
    card_expiry: str  # ex: "12/25"
    card_cvv: str


class ShippingAddressRequest(BaseModel):
    # Endereço de entrega do pedido
    street: str
    number: str
    city: str
    state: str
    zip_code: str


class ItemRequest(BaseModel):
    # Representa um produto no carrinho
    product_id: int
    quantity: int
    price: float


class CheckoutRequest(BaseModel):
    # Corpo completo da requisição POST /checkout
    # Agrupa tudo que é necessário para processar um pedido: pagamento, cliente, endereço e itens
    payment_method: PaymentMethodRequest
    customer_email: str
    shipping_address: ShippingAddressRequest
    items: ItemRequest
