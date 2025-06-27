from token import OP
import requests
from typing import Dict, Optional, List
from datetime import datetime
from chainsettle_sdk.config import get_settings
from chainsettle_sdk.utils.error_handler import handle_api_error
import time
import json
import secrets

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
        self.id_hash = None
        self.ramp_contract = None

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
        response = requests.get(f"{self.base_url}/api/settlement_types")
        response.raise_for_status()
        data = response.json()

        self.supported_apis = data.get("supported_types", [])
        self.supported_networks = data.get("supported_networks", [])
        self.supported_asset_categories = data.get("supported_asset_categories", [])
        self.supported_jurisdictions = data.get("supported_jurisdictions", [])

        return data

    @handle_api_error
    def initiate_attestation(
        self,
        settlement_type: str,
        network: str,
        user_email: str,
        settlement_id: Optional[str] = None,
        amount: Optional[float] = 0.0,
        witness: Optional[str] = None,
        counterparty: Optional[str] = None,
        details: Optional[str] = None,
        recipient_email: Optional[str] = None,
    ) -> Dict:
        """
        Initiates the attestation process for a settlement.
        """
        if settlement_id is None:
            settlement_id = secrets.token_hex(4)
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
            "user_email": user_email,
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

        self.id_hash = response.json().get('settlement_info').get("id_hash")

        if self.id_hash:
            print(f"Settlement initiated with ID Hash: {self.id_hash}")
            
        return response.json()
    
    @handle_api_error
    def attest_settlement(self, id_hash: Optional[str] = None):
        """
        Attests a settlement with the given ID.
        """
        if id_hash is None:
            if self.id_hash is None:
                raise ValueError("No ID hash provided and no previous ID hash available.")
            id_hash = self.id_hash
        payload = {
            "id_hash": id_hash,
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
    def get_settlement_status(self, id_hash: Optional[str] = None) -> Optional[int]:
        """
        Obtains the status of a settlement.
        If the HTTP response is not 200, returns None instead of raising.
        """
        if id_hash is None:
            if self.id_hash is None:
                raise ValueError("No ID hash provided and no previous ID hash available.")
            id_hash = self.id_hash

        response = requests.get(
            f"{self.base_url}/api/get_settlement_status/{id_hash}"
        )
        if response.status_code != 200:
            return None

        payload = response.json()
        return payload.get("status")

    @handle_api_error
    def get_settlement_info(self, id_hash: Optional[str] = None) -> Dict:
        """
        Retrieves detailed information about a settlement.
        If the HTTP response is not 200, returns an empty dictionary.
        """

        if id_hash is None:
            if self.id_hash is None:
                raise ValueError("No ID hash provided and no previous ID hash available.")
            id_hash = self.id_hash

        response = requests.get(f"{self.base_url}/api/get_settlement/{id_hash}")
        if response.status_code != 200:
            return {}

        payload = response.json().get("data", {})
        return payload
        
    @handle_api_error
    def get_validator_list(self):
        """
        Retrieves the list of available validators.
        """
        response = requests.get(f"{self.base_url}/api/validator_list")
        response.raise_for_status()
        return response.json()
        
    @handle_api_error
    def simulate_signing(self, envelope_id: str, recipient_id: str) -> Dict:
        """
        Simulates the signing of an envelope by a specific recipient.
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
    def store_salt(self, salt: str,
                   email: str, recipient_email: str,
                   id_hash: Optional[str] = None) -> Dict:
        """
        Stores a salt for a specific settlement.
        """

        if id_hash is None:
            if self.id_hash is None:
                raise ValueError("No ID hash provided and no previous ID hash available.")
            id_hash = self.id_hash

        payload = {
            "id_hash": id_hash,
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
        id_hash: Optional[str] = None,
        statuses: Optional[List[int]] = None,
        interval: float = 5.0,
        max_attempts: int = 120
        ) -> Dict:
            """
            Polls the API until the settlement reaches one of the given statuses,
            and then returns the full settlement-info dictionary.

            Even if get_settlement_status(...) raises a 404 or similar “not found yet” error,
            we catch it below, sleep, and retry until max_attempts.
            """
            if id_hash is None:
                if self.id_hash is None:
                    raise ValueError("No ID hash provided and no previous ID hash available.")
                id_hash = self.id_hash

            if statuses is None:
                statuses = [3, 4]  # e.g. 3=confirmed, 4=failed

            for attempt in range(1, max_attempts + 1):
                try:
                    status_code = self.get_settlement_status(id_hash)
                    if status_code is None:
                        print(f"[Attempt {attempt}] status endpoint returned None (not found). Retrying in {interval}s...")
                        print("Ensure the salt is stored off-chain before polling.")
                        time.sleep(interval)
                        continue
                except requests.exceptions.RequestException as e:
                    if hasattr(e, "response") and e.response is not None:
                        code = e.response.status_code
                        if code == 404:
                            print(f"[Attempt {attempt}] status endpoint returned 404 (not created yet). Retrying in {interval}s...")
                            time.sleep(interval)
                            continue
                        else:
                            print(f"[Attempt {attempt}] HTTP error {code} when fetching status. Retrying in {interval}s...")
                            time.sleep(interval)
                            continue
                    else:
                        print(f"[Attempt {attempt}] error fetching status: {e}. Retrying in {interval}s...")
                        time.sleep(interval)
                        continue

                if status_code in statuses:
                    try:
                        info = self.get_settlement_info(id_hash)
                        return info.get("data", info)
                    except requests.exceptions.RequestException as e:
                        print(f"[Attempt {attempt}] error fetching info: {e}. Retrying in {interval}s...")
                        time.sleep(interval)
                        continue

                print(f"[Attempt {attempt}] status {status_code} is not in {statuses} → waiting {interval}s to retry...")
                time.sleep(interval)

            raise TimeoutError(
                f"Settlement '{id_hash}' did not reach statuses {statuses} "
                f"after {max_attempts} attempts ({max_attempts * interval:.0f}s)."
            )

    def poll_settlement_status_onchain(self, 
        ramp_contract: Optional[object] = None, 
        id_hash_bytes: Optional[bytes] = None,
        max_attempts: Optional[int] = 60, 
        delay: Optional[int] = 5,
        statuses: Optional[List[int]] = [3, 4]) -> int:
        """
        Polls the on-chain settlement status every 5 seconds for up to 5 minutes (default).
        Exits early if the status reaches 3 (Confirmed) or 4 (Failed).
        """
        status = None
        
        if id_hash_bytes is None:
            if self.id_hash is None:
                raise ValueError("No ID hash provided and no previous ID hash available.")
            id_hash_bytes = bytes.fromhex(self.id_hash)
        
        if ramp_contract is None:
            if self.ramp_contract is None:
                raise ValueError("No ramp contract provided and no previous contract available.")
            ramp_contract = self.ramp_contract

        print(f"Polling settlement status for idHash: {id_hash_bytes.hex()} ...")
        for attempt in range(1, max_attempts + 1):
            # Fetch on-chain status
            status = ramp_contract.functions.getSettlementStatus(id_hash_bytes).call()
            print(f"[Attempt {attempt}] status: {status}")
            
            # If status is Confirmed (3) or Failed (4), exit early
            if status in statuses:
                print(f"Settlement finalized with status: {status}")
                return status
            
            # Wait before next attempt
            time.sleep(delay)
        else:
            print("Polling timed out after 5 minutes.")
            return status
