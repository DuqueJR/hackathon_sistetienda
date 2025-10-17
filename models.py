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
    """Datos del cliente capturados vía WhatsApp"""
    telefono: str = Field(..., description="Número de teléfono")
    direccion: Optional[str] = Field(None, description="Dirección del cliente")
    ingresos_mensuales: Optional[float] = Field(None, description="Ingresos mensuales del cliente")
    trabajo: Optional[str] = Field(None, description="Trabajo del cliente")
    psych_organized: int = Field(..., ge=1, le=5, description="Evaluación psicométrica de organización (1-5)")
    psych_plan: int = Field(..., ge=1, le=5, description="Evaluación psicométrica de planificación (1-5)")

class StoreValidation(BaseModel):
    """Validación del tendero sobre el cliente"""
    cedula_cliente: str = Field(..., description="Cédula del cliente")
    nombre_cliente: str = Field(..., description="Nombre del cliente")
    know_buyer: int = Field(..., ge=0, le=5, description="Tiempo que conoce al cliente (0-5)")
    buy_freq: int = Field(..., ge=0, le=5, description="Frecuencia de compra (0-5)")
    avg_purchase: float = Field(..., gt=0, description="Monto promedio de compra")
    distance_km: Optional[float] = Field(None, ge=0, description="Distancia en km (opcional)")
    address_verified: Optional[bool] = Field(None, description="Dirección verificada (opcional)")

class Transaction(BaseModel):
    token: str = Field(..., description="Token único de la transacción")
    status: TransactionStatus = Field(default=TransactionStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime = Field(..., description="Fecha de expiración")
    client_data: Optional[ClientData] = Field(None)
    store_validation: Optional[StoreValidation] = Field(None)
    credit_result: Optional[Dict[str, Any]] = Field(None)

class InitiateTransactionRequest(BaseModel):
    store_id: str = Field(..., description="ID de la tienda")
    tendero_name: str = Field(..., description="Nombre del tendero")

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
    telefono: str
    direccion: Optional[str] = None
    ingresos_mensuales: Optional[float] = None
    trabajo: Optional[str] = None
    psych_organized: int = Field(..., ge=1, le=5)
    psych_plan: int = Field(..., ge=1, le=5)

class POSWebhookRequest(BaseModel):
    token: str
    cedula_cliente: str
    nombre_cliente: str
    know_buyer: int = Field(..., ge=0, le=5)
    buy_freq: int = Field(..., ge=0, le=5)
    avg_purchase: float = Field(..., gt=0)
    distance_km: Optional[float] = Field(None, ge=0)
    address_verified: Optional[bool] = None

class TransactionStatusResponse(BaseModel):
    status: TransactionStatus
    result: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

class CreditResult(BaseModel):
    """Resultado del análisis crediticio usando el modelo Micro v2"""
    category: str = Field(..., description="Categoría crediticia (A, B, C, D, E)")
    score_conf: float = Field(..., ge=0, le=1, description="Puntaje de confianza (0-1)")
    risk_pct: float = Field(..., ge=0, le=100, description="Porcentaje de riesgo")
    debt_capacity_pct: float = Field(..., ge=0, le=1, description="Capacidad de deuda")
    cupo_estimated: float = Field(..., ge=0, description="Cupo estimado")
    raw_cupo: float = Field(..., description="Cupo crudo antes de ajustes")
    comp_feature: float = Field(..., description="Componente basado en features")
    comp_income: float = Field(..., description="Componente basado en proxy de ingreso")
    features: Dict[str, Any] = Field(..., description="Features normalizados")
    clients_per_day: int = Field(..., description="Clientes por día estimados")
    income_proxy_daily: float = Field(..., description="Proxy de ingreso diario")
