import os

import httpx

from app.checkout.checkout_request import (
    ItemRequest,
)


class InventoryClient:
    def __init__(self):
        self.inventory_service_url = os.getenv("INVENTORY_SERVICE_URL")
        self.client = httpx.AsyncClient(base_url=self.inventory_service_url)

    async def deduct_inventory(
        self,
        items: list[ItemRequest],
    ):
        try:
            payload = {
                "items": [
                    {
                        "product_id": item.product_id,
                        "quantity": item.quantity,
                    }
                    for item in items
                ]
            }
            response = await self.client.post("/inventory/deduct", json=payload)
            response.raise_for_status()
            return {"success": True, "error": None}
        except httpx.ConnectError:
            return {"success": False, "error": "Inventory service unavailable"}
        except httpx.TimeoutException:
            return {"success": False, "error": "Inventory service timeout"}
        except httpx.HTTPStatusError as e:
            return {"success": False, "error": e.response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}



def get_inventory_client() -> InventoryClient:
    return InventoryClient()
