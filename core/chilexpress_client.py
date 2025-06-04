# webapp/chilexpress_client.py

import requests
from typing import Optional

class ChilexpressClient:
    BASE_URL = "https://testservices.wschilexpress.com"
    RATE_ENDPOINT = "/rating/api/v1.0/rates/courier"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def calculate_shipping(
        self,
        origin_county_code: str,
        destination_county_code: str,
        package_weight: float,
        is_delivery: bool = True,
        declared_worth: float = 0.0
    ) -> Optional[dict]:
        """
        Calcula el costo de envío usando el endpoint de Courier de Chilexpress (sandbox).
        Usa el mismo payload que en el ejemplo de la documentación:

        {
            "originCountyCode": "STGO",
            "destinationCountyCode": "PROV",
            "package": {
                "weight": "16",
                "height": "1",
                "width": "1",
                "length": "1"
            },
            "productType": 3,
            "contentType": 1,
            "declaredWorth": "2333",
            "deliveryTime": 0
        }
        """

        url = f"{self.BASE_URL}{self.RATE_ENDPOINT}"        
        headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "Ocp-Apim-Subscription-Key": self.api_key
        }

        # En el ejemplo de la documentación, usan strings para peso/dimensiones.
        # Aquí convertimos el peso a string para imitar exactamente ese formato.
        payload = {            "originCountyCode": str(origin_county_code),      # Ej: "13101"
            "destinationCountyCode": str(destination_county_code), # Ej: "13123"
            "package": {
                "weight": str(package_weight),
                "height": "10",
                "width": "10",
                "length": "10"
            },
            "productType": 3 if is_delivery else 2,  # 3=entrega a domicilio, 2=pickup
            "contentType": 1,                        # Siempre 1 en el ejemplo
            "declaredWorth": str(declared_worth),    # Ej: "0" o "2333"
            "deliveryTime": 0                        # 0 = normal
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            # El ejemplo devuelve:
            # {
            #   "data": {
            #     "courierServiceOptions": [
            #        { "serviceTypeCode": 41, "serviceDescription": "...",
            #          "serviceValue": "8715", … },
            #        { … }
            #     ]
            #   },
            #   "statusCode": 0, "statusDescription": "OK", "errors": null
            # }
            if data.get("statusCode") == 0 and data.get("data", {}).get("courierServiceOptions"):
                options = data["data"]["courierServiceOptions"]
                # Elegimos la opción más barata (menor serviceValue)
                cheapest = min(options, key=lambda x: float(x["serviceValue"]))
                return {
                    "cost": float(cheapest["serviceValue"]),
                    "service_type": cheapest["serviceDescription"],
                    "service_description": cheapest.get("conditions", ""),
                    "delivery_time": cheapest.get("deliveryTime", "")
                }
            else:
                # Si statusCode != 0, devolvemos un error con el mensaje
                msg = data.get("statusDescription", "Error desconocido en Chilexpress")
                raise ValueError(f"Chilexpress error: {msg}")

        except requests.exceptions.RequestException as e:
            raise ValueError(f"Error de conexión con Chilexpress: {str(e)}")
        except (KeyError, ValueError) as e:
            raise ValueError(str(e))
        except Exception as e:
            raise ValueError(f"Error inesperado: {str(e)}")
