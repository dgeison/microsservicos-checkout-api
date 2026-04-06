import os

import httpx

from app.checkout.checkout_request import PaymentMethodRequest


class PaymentClient:
    def __init__(self):
        self.payment_service_url = os.getenv("PAYMENT_SERVICE_URL")
        self.client = httpx.AsyncClient(base_url=self.payment_service_url)

    async def process(
        self,
        total_amount: float,
        payment_method: PaymentMethodRequest,
        customer_email: str,
    ):
        try:
            payload = {
                "amount": total_amount,
                "payment_method": {
                    "type": payment_method.type,
                    "card_number": payment_method.card_number,
                    "card_expiry": payment_method.card_expiry,
                    "card_cvv": payment_method.card_cvv,
                },
                "customer_email": customer_email,
            }
            response = await self.client.post("payments/process", json=payload)
            response.raise_for_status()
            transaction_id = response.json()["transactionId"]
            return {"transaction_id": transaction_id, "error": None}
        except httpx.HTTPStatusError as e:
            error_response = e.response.text
            return {"transaction_id": None, "error": error_response}
        except Exception as e:
            return {"transaction_id": None, "error": str(e)}


def get_payment_client() -> PaymentClient:
    return PaymentClient()
