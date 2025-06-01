import hashlib
import json
from typing import Any, Dict

def generate_escrow_id(payer_address: str, amount: float, timestamp: int) -> str:
    """
    Genera un ID único para el escrow basado en los parámetros del pago
    """
    data = f"{payer_address}{amount}{timestamp}"
    return hashlib.sha256(data.encode()).hexdigest()

def format_payment_data(payment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formatea los datos del pago para asegurar consistencia
    """
    return {
        "amount": float(payment_data.get("amount", 0)),
        "currency": payment_data.get("currency", "USD"),
        "status": payment_data.get("status", "pending"),
        "timestamp": payment_data.get("timestamp", 0)
    }

def validate_payment_amount(amount: float) -> bool:
    """
    Valida que el monto del pago sea válido
    """
    return amount > 0 and amount <= 1000000  # Límite arbitrario de 1M USD

def create_payment_signature(payment_data: Dict[str, Any], secret_key: str) -> str:
    """
    Crea una firma para los datos del pago
    """
    data_string = json.dumps(payment_data, sort_keys=True)
    return hashlib.sha256(f"{data_string}{secret_key}".encode()).hexdigest() 