import requests
from typing import Dict, Optional, List
from datetime import datetime
from chainsettle_sdk.config import get_settings
from chainsettle_sdk.utils.error_handler import handle_api_error
import time
import json

global settings
settings = get_settings()

class ChainSettleService:
    def __init__(self):
        self.base_url = settings.CHAINSETTLE_API_URL
        self.akash_url = settings.CHAINSETTLE_AKASH_URL
        self.supported_networks = settings.CHAINSETTLE_SUPPORTED_NETWORKS
        self.supported_apis = settings.CHAINSETTLE_SUPPORTED_APIS
        self.supported_asset_categories = settings.CHAINSETTLE_SUPPORTED_ASSET_CATEGORIES
        self.supported_jurisdictions = settings.CHAINSETTLE_SUPPORTED_JURISDICTIONS
        self.zero_address = settings.ZERO_ADDRESS

        self.get_settlement_types()
        print(f"ChainSettle Node {'live' if self.is_ok() else 'not responding'} at {self.base_url}")

    @handle_api_error
    def is_ok(self):
        r = requests.get(f"{self.base_url}/api/health")
        if r.json().get("status") == "ok":
            return True
        
    @handle_api_error
    def get_settlement_types(self) -> Dict:
        """
        Fetch supported settlement types and networks from ChainSettle.
        """
        # correct endpoint name: /api/settlement_types
        response = requests.get(f"{self.base_url}/api/settlement_types")
        response.raise_for_status()
        data = response.json()

        # backend returns keys: supported_types, supported_networks, supported_asset_categories, supported_jurisdictions
        self.supported_apis = data.get("supported_types", [])
        self.supported_networks = data.get("supported_networks", [])
        self.supported_asset_categories = data.get("supported_asset_categories", [])
        self.supported_jurisdictions = data.get("supported_jurisdictions", [])

        return data

    @handle_api_error
    def initiate_attestation(
        self,
        settlement_id: str,
        settlement_type: str,
        network: str,
        user_email: str,
        amount: Optional[float] = 0.0,
        witness: Optional[str] = None,
        counterparty: Optional[str] = None,
        details: Optional[str] = None,
        recipient_email: Optional[str] = None,
    ) -> Dict:
        """
        Inicia el proceso de attestación para un settlement.
        """
        if witness is None:
            witness = self.zero_address
        if counterparty is None:
            counterparty = self.zero_address
        if details is None:
            details = ""
        if recipient_email is None:
            recipient_email = ""

        payload = {
            "settlement_id": settlement_id,
            "notify_email": user_email,
            "settlement_type": settlement_type,
            "network": network,
            "amount": amount,
            "witness": witness,
            "counterparty": counterparty,
            "details": details,
            "recipient_email": recipient_email,
        }

        response = requests.post(
            f"{self.base_url}/api/init_attestation",
            json=payload
        )
        response.raise_for_status()
            
        return response.json()
    
    @handle_api_error
    def attest_settlement(self,
                          settlement_id: str
    ):
        
        payload = {
            "settlement_id":settlement_id,
        }
        try:
            res = requests.post(f"{self.base_url}/api/attest_settlement", json=payload)
            res.raise_for_status()
            data = res.json()

            if 'internal_status' not in data or data['internal_status'] != 'attested':
                print("Unexpected response from backend. Settlement may not be valid or pending further action.")

            return data
        except requests.exceptions.RequestException as e:
            if e.response is not None:
                try:
                    err = e.response.json().get("error") or e.response.text
                    print(f"Attestation request failed: {err}")
                except Exception:
                    print(f"Attestation request failed with status {e.response.status_code}")
            else:
                print(f"Attestation request failed: {e}")

    @handle_api_error
    def get_settlement_status(self, settlement_id: str) -> Optional[int]:
        """
        Obtiene el estado actual de un settlement.
        Si la respuesta HTTP no es 200, devuelve None en lugar de lanzar.
        """
        response = requests.get(
            f"{self.base_url}/api/get_settlement_status/{settlement_id}"
        )
        if response.status_code != 200:
            # No data yet (404) or some other transient error → return None
            return None

        payload = response.json()
        # La API devuelve {"status": <int>} bajo HTTP 200
        return payload.get("status")

    @handle_api_error
    def get_settlement_info(self, settlement_id: str) -> Dict:
        """
        Obtiene información detallada de un settlement.
        Si la respuesta HTTP no es 200, devuelve {}.
        """
        response = requests.get(f"{self.base_url}/api/get_settlement/{settlement_id}")
        if response.status_code != 200:
            # No data yet or error → return empty dict
            return {}

        payload = response.json().get("data", {})
        return payload
        
    @handle_api_error
    def get_validator_list(self):
        """
        Obtiene la lista de validadores disponibles.
        """
        response = requests.get(f"{self.base_url}/api/validator_list")
        response.raise_for_status()
        return response.json()
        
    @handle_api_error
    def simulate_signing(
        self,
        envelope_id: str,
        recipient_id: str
    ) -> Dict:
        """
        Simula la firma de un sobre por un destinatario específico.
        """
        payload = {
            "envelope_id": envelope_id,
            "recipient_id": recipient_id
        }
        
        response = requests.post(
            f"{self.base_url}/api/simulate_signing",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    @handle_api_error
    def store_salt(self, settlement_id: str, salt: str,
                   email: str, recipient_email: str) -> Dict:
        """
        Almacena un salt para un settlement específico.
        """
        payload = {
            "settlement_id": settlement_id,
            "salt": salt,
            "email": email,
            "recipient_email": recipient_email
        }
        
        response = requests.post(
            f"{self.base_url}/api/store_salt",
            json=payload
        )
        response.raise_for_status()
        return response.json()
        
    @handle_api_error
    def poll_settlement_activity(
    self,
    settlement_id: str,
    statuses: Optional[List[int]] = None,
    interval: float = 5.0,
    max_attempts: int = 120
    ) -> Dict:
        """
        Polls the API until the settlement reaches one of the given statuses,
        and then returns the full settlement-info dict.

        Even if get_settlement_status(...) raises a 404 or similar “not found yet” error,
        we catch it below, sleep, and retry until max_attempts.
        """
        if statuses is None:
            statuses = [3, 4]  # e.g. 3=attested, 4=finalized

        for attempt in range(1, max_attempts + 1):
            # --- STEP 1: Try to fetch the status_code, but catch HTTP errors ---
            try:
                status_code = self.get_settlement_status(settlement_id)
                print(f"[Attempt {attempt}] settlement status: {status_code}")
            except requests.exceptions.RequestException as e:
                # If the endpoint returns 404 (or any 4xx/5xx), treat as “not ready yet”
                if hasattr(e, "response") and e.response is not None:
                    code = e.response.status_code
                    # 404 means “not found yet in our off-chain cache” → sleep & retry
                    if code == 404:
                        print(f"[Attempt {attempt}] status endpoint returned 404 (not created yet). Retrying in {interval}s...")
                        time.sleep(interval)
                        continue
                    else:
                        # Other HTTP errors (500, etc.) → also retry, but log
                        print(f"[Attempt {attempt}] HTTP error {code} when fetching status. Retrying in {interval}s...")
                        time.sleep(interval)
                        continue
                else:
                    # Non-HTTP exception (network issue, timeout, etc.) → retry
                    print(f"[Attempt {attempt}] error fetching status: {e}. Retrying in {interval}s...")
                    time.sleep(interval)
                    continue

            # --- STEP 2: If we do get a status_code, check if it’s terminal ---
            if status_code in statuses:
                # STEP 3: Try to fetch detailed info now that we know it’s terminal
                try:
                    info = self.get_settlement_info(settlement_id)
                    # If our API wraps everything under "data", unwrap it
                    return info.get("data", info)
                except requests.exceptions.RequestException as e:
                    # Maybe the info endpoint isn’t ready even though status is. Retry a few times.
                    print(f"[Attempt {attempt}] error fetching info: {e}. Retrying in {interval}s...")
                    time.sleep(interval)
                    continue

            # Not yet in a terminal status → sleep then loop again
            print(f"[Attempt {attempt}] status {status_code} is not in {statuses} → waiting {interval}s to retry...")
            time.sleep(interval)

        # If we reach max_attempts without hitting a terminal status
        raise TimeoutError(
            f"Settlement '{settlement_id}' did not reach statuses {statuses} "
            f"after {max_attempts} attempts ({max_attempts * interval:.0f}s)."
        )
