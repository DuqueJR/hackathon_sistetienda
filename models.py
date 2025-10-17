from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class TransactionStatus(str, Enum):
    PENDING = "pending"
    CLIENT_DATA_RECEIVED = "client_data_received"
    STORE_VALIDATION_RECEIVED = "store_validation_received"
    PROCESSING = "processing"
    COMPLETED = "completed"
    EXPIRED = "expired"
    ERROR = "error"

class ClientData(BaseModel):
    cedula: str = Field(..., description="Cédula del cliente")
    nombre: str = Field(..., description="Nombre completo del cliente")
    telefono: str = Field(..., description="Número de teléfono")
    direccion: Optional[str] = Field(None, description="Dirección del cliente")
    ingresos_mensuales: Optional[float] = Field(None, description="Ingresos mensuales del cliente")
    trabajo: Optional[str] = Field(None, description="Trabajo del cliente")

class StoreValidation(BaseModel):
    cedula: str = Field(..., description="Cédula del cliente")
    nombre: str = Field(..., description="Nombre del cliente")
    tiempo_cliente: str = Field(..., description="Tiempo que conoce al cliente")
    frecuencia_compra: str = Field(..., description="Frecuencia de compra")
    monto_promedio: float = Field(..., description="Monto promedio de compra")
    confianza: int = Field(..., ge=1, le=10, description="Nivel de confianza del 1 al 10")

class Transaction(BaseModel):
    token: str = Field(..., description="Token único de la transacción")
    status: TransactionStatus = Field(default=TransactionStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime = Field(..., description="Fecha de expiración")
    client_data: Optional[ClientData] = Field(None)
    store_validation: Optional[StoreValidation] = Field(None)
    trust_score: Optional[int] = Field(None, ge=0, le=100)
    credit_result: Optional[Dict[str, Any]] = Field(None)

class InitiateTransactionRequest(BaseModel):
    pass  # No necesita datos adicionales

class InitiateTransactionResponse(BaseModel):
    token: str
    qr_url: str
    expires_at: datetime

class ValidateTokenRequest(BaseModel):
    token: str

class ValidateTokenResponse(BaseModel):
    valid: bool
    status: Optional[TransactionStatus] = None
    expires_at: Optional[datetime] = None

class WhatsAppWebhookRequest(BaseModel):
    token: str
    cedula: str
    nombre: str
    telefono: str
    direccion: Optional[str] = None
    ingresos_mensuales: Optional[float] = None
    trabajo: Optional[str] = None

class POSWebhookRequest(BaseModel):
    token: str
    cedula: str
    nombre: str
    tiempo_cliente: str
    frecuencia_compra: str
    monto_promedio: float
    confianza: int

class TransactionStatusResponse(BaseModel):
    status: TransactionStatus
    result: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

class CreditResult(BaseModel):
    aprobado: bool
    monto: Optional[float] = None
    puntaje: int
    motivo: Optional[str] = None
