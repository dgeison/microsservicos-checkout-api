import asyncio

import httpx

from app.client_manager import client_manager
from app.checkout.checkout_request import PaymentMethodRequest


class PaymentClient:
    def __init__(self, client: httpx.AsyncClient, max_retries: int = 3):
        self.client = client
        self.max_retries = max_retries

    async def process(
        self,
        total_amount: float,
        payment_method: PaymentMethodRequest,
        customer_email: str,
    ):
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

        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = await self.client.post("payments/process", json=payload)
                response.raise_for_status()
                transaction_id = response.json()["transactionId"]
                return {"transaction_id": transaction_id, "error": None}
            except httpx.HTTPStatusError as e:
                if 400 <= e.response.status_code < 500:
                    # Erros do cliente (ex: dados de pagamento inválidos) não devem ser re-tentados
                    error_response = e.response.text
                    return {"transaction_id": None, "error": error_response}
                last_error = e.response.text
            except (httpx.RequestError, httpx.TimeoutException) as e:
                last_error = str(e)
            except Exception as e:
                return {"transaction_id": None, "error": str(e)}

            if attempt < self.max_retries - 1:
                wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s...
                await asyncio.sleep(wait_time)

        return {
            "transaction_id": None,
            "error": f"Payment processing failed after {self.max_retries} attempts: {last_error}",
        }


def get_payment_client() -> PaymentClient:
    return PaymentClient(client=client_manager.payment_client)
