import requests
from typing import Dict, Optional, List
from datetime import datetime
from config import settings
from utils.error_handler import handle_api_error
import time

class ChainSettleService:
    def __init__(self):
        self.base_url = settings.CHAINSETTLE_API_URL
        self.akash_url = settings.CHAINSETTLE_AKASH_URL
        self.supported_networks = settings.CHAINSETTLE_SUPPORTED_NETWORKS
        self.supported_apis = settings.CHAINSETTLE_SUPPORTED_APIS
        self.supported_asset_categories = settings.CHAINSETTLE_SUPPORTED_ASSET_CATEGORIES
        self.supported_jurisdictions = settings.CHAINSETTLE_SUPPORTED_JURISDICTIONS

        self.get_settlement_types(self)
        
    @handle_api_error
    def get_settlement_types(self):
        """
        Obtiene los tipos de settlement soportados por ChainSettle.
        """
        response = requests.get(f"{self.base_url}/api/get_settlement_types")
        response.raise_for_status()
        data = response.json()

        self.supported_networks = data.get("supported_networks", [])
        self.supported_apis = data.get("supported_apis", [])
        self.supported_asset_categories = data.get("supported_asset_categories", [])
        self.supported_jurisdictions = data.get("supported_jurisdictions", [])

        return data

    @handle_api_error
    def register_settlement(
        self,
        settlement_id: str,
        network: str,
        settlement_type: str,
        amount: float,
        recipient_email: str,
        payer: Optional[str] = None,
        metadata: Optional[Dict] = None,
        notify_email: Optional[str] = None
    ) -> Dict:
        """
        Registra un nuevo settlement en ChainSettle.
        """
        if network not in self.supported_networks:
            raise ValueError(f"Red no soportada. Redes soportadas: {self.supported_networks}")
        
        if settlement_type not in self.supported_apis:
            raise ValueError(f"Tipo de settlement no soportado. Tipos soportados: {self.supported_apis}")

        payload = {
            "settlement_id": settlement_id,
            "network": network,
            "settlement_type": settlement_type,
            "amount": amount,
            "recipient_email": recipient_email,
            "payer": payer
        }

        if metadata:
            payload["metadata"] = metadata
        if notify_email:
            payload["notify_email"] = notify_email

        response = requests.post(
            f"{self.base_url}/api/register_settlement",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    @handle_api_error
    def initiate_attestation(
        self,
        settlement_id: str,
    ) -> Dict:
        """
        Inicia el proceso de attestación para un settlement.
        """
        payload = {
            "settlement_id": settlement_id
        }

        response = requests.post(
            f"{self.base_url}/api/initiate_attestation",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    @handle_api_error
    def get_settlement_status(self, settlement_id: str) -> Dict:
        """
        Obtiene el estado actual de un settlement.
        """
        response = requests.get(
            f"{self.base_url}/api/get_settlement/{settlement_id}"
        )
        response.raise_for_status()
        return response.json()

    @handle_api_error
    def poll_settlement_activity(
        self,
        settlement_id: str,
        interval: int = 30,
        max_attempts: int = 20
    ) -> List[Dict]:
        """
        Monitorea la actividad de un settlement hasta que se complete o se alcance el máximo de intentos.
        """
        transactions = []
        attempts = 0

        while attempts < max_attempts:
            status = self.get_settlement_status(settlement_id)
            
            if status.get("status") in ["verified", "failed"]:
                break

            # Buscar transacciones en el estado
            for tx_type in ["Init", "Attest", "Validate"]:
                tx_hash = status.get(f"{tx_type.lower()}_tx_hash")
                if tx_hash and tx_hash not in [t.get("hash") for t in transactions]:
                    transactions.append({
                        "type": tx_type,
                        "hash": tx_hash,
                        "url": f"https://base-sepolia.blockscout.com/tx/{tx_hash}"
                    })

            attempts += 1
            time.sleep(interval)

        return transactions

    def attest_settlement(self, settlement_id: str) -> Dict[str, Any]:
        """
        Start the attestation process for a settlement
        """
        # Implementation here
        return {"status": "success"} 