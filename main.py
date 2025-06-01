from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict
import os
from dotenv import load_dotenv
from .services.chainsettle import ChainSettleService
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

app = FastAPI(
    title="Settlement Ramp API",
    description="API para el sistema de Settlement Ramp",
    version="1.0.0"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar los orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas
@app.get("/")
async def root():
    return {"message": "Bienvenido a Settlement Ramp API"}

@app.post("/api/settlements/register")
async def register_settlement(
    settlement_id: str,
    network: str,
    settlement_type: str,
    amount: float,
    recipient_email: str,
    metadata: Optional[Dict] = None,
    notify_email: Optional[str] = None
):
    """
    Registra un nuevo settlement en ChainSettle.
    """
    chainsettle = ChainSettleService()
    result = chainsettle.register_settlement(
        settlement_id=settlement_id,
        network=network,
        settlement_type=settlement_type,
        amount=amount,
        recipient_email=recipient_email,
        metadata=metadata,
        notify_email=notify_email
    )
    return result

@app.post("/api/settlements/{settlement_id}/attest")
async def attest_settlement(
    settlement_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """
    Inicia el proceso de attestación para un settlement.
    """
    chainsettle = ChainSettleService()
    result = chainsettle.initiate_attestation(
        settlement_id=settlement_id,
        start_date=start_date,
        end_date=end_date
    )
    return result

@app.get("/api/settlements/{settlement_id}/status")
async def get_settlement_status(settlement_id: str):
    """
    Obtiene el estado actual de un settlement.
    """
    chainsettle = ChainSettleService()
    result = chainsettle.get_settlement_status(settlement_id)
    return result

@app.get("/api/settlements/{settlement_id}/activity")
async def get_settlement_activity(
    settlement_id: str,
    interval: int = 30,
    max_attempts: int = 20
):
    """
    Monitorea la actividad de un settlement.
    """
    chainsettle = ChainSettleService()
    result = chainsettle.poll_settlement_activity(
        settlement_id=settlement_id,
        interval=interval,
        max_attempts=max_attempts
    )
    return result

@app.post("/attest")
async def attest_payment(settlement_id: str):
    """
    Start the attestation process for a settlement
    """
    try:
        # Implementation here
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 