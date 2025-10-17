from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import uuid
from models import Transaction, TransactionStatus, ClientData, StoreValidation, CreditResult

# Almacén en memoria para las transacciones
transactions_storage: Dict[str, Transaction] = {}

def generate_token() -> str:
    """Genera un token único para la transacción"""
    return str(uuid.uuid4())

def create_transaction() -> Transaction:
    """Crea una nueva transacción con token y fecha de expiración"""
    token = generate_token()
    expires_at = datetime.now() + timedelta(minutes=15)  # 15 minutos de expiración
    
    transaction = Transaction(
        token=token,
        expires_at=expires_at
    )
    
    transactions_storage[token] = transaction
    return transaction

def get_transaction(token: str) -> Optional[Transaction]:
    """Obtiene una transacción por su token"""
    return transactions_storage.get(token)

def update_transaction(token: str, **kwargs) -> bool:
    """Actualiza una transacción existente"""
    if token not in transactions_storage:
        return False
    
    transaction = transactions_storage[token]
    for key, value in kwargs.items():
        if hasattr(transaction, key):
            setattr(transaction, key, value)
    
    return True

def is_token_valid(token: str) -> bool:
    """Verifica si un token es válido y no ha expirado"""
    transaction = get_transaction(token)
    if not transaction:
        return False
    
    return datetime.now() < transaction.expires_at

def calculate_trust_score(transaction: Transaction) -> CreditResult:
    """
    Calcula el puntaje de confianza basado en los datos del cliente y validación del tendero
    """
    if not transaction.client_data or not transaction.store_validation:
        return CreditResult(
            aprobado=False,
            puntaje=0,
            motivo="Faltan datos del cliente o validación del tendero"
        )
    
    score = 0
    client_data = transaction.client_data
    store_validation = transaction.store_validation
    
    # Puntos por tiempo de relación con el cliente (máximo 25 puntos)
    tiempo_puntos = {
        "menos-6-meses": 5,
        "6-meses-1-ano": 10,
        "1-2-anos": 15,
        "mas-2-anos": 25
    }
    score += tiempo_puntos.get(store_validation.tiempo_cliente, 0)
    
    # Puntos por frecuencia de compra (máximo 20 puntos)
    frecuencia_puntos = {
        "diaria": 20,
        "semanal": 15,
        "quincenal": 10,
        "mensual": 5
    }
    score += frecuencia_puntos.get(store_validation.frecuencia_compra, 0)
    
    # Puntos por monto promedio (máximo 15 puntos)
    if store_validation.monto_promedio >= 100000:
        score += 15
    elif store_validation.monto_promedio >= 50000:
        score += 10
    elif store_validation.monto_promedio >= 20000:
        score += 5
    
    # Puntos por nivel de confianza del tendero (máximo 20 puntos)
    score += store_validation.confianza * 2
    
    # Puntos por ingresos del cliente (máximo 20 puntos)
    if client_data.ingresos_mensuales:
        if client_data.ingresos_mensuales >= 2000000:
            score += 20
        elif client_data.ingresos_mensuales >= 1000000:
            score += 15
        elif client_data.ingresos_mensuales >= 500000:
            score += 10
        elif client_data.ingresos_mensuales >= 300000:
            score += 5
    
    # Determinar aprobación (mínimo 60 puntos para aprobar)
    aprobado = score >= 60
    
    # Calcular monto del crédito si es aprobado
    monto = None
    if aprobado:
        if score >= 80:
            monto = min(500000, client_data.ingresos_mensuales * 0.3 if client_data.ingresos_mensuales else 200000)
        elif score >= 70:
            monto = min(300000, client_data.ingresos_mensuales * 0.2 if client_data.ingresos_mensuales else 150000)
        else:
            monto = min(200000, client_data.ingresos_mensuales * 0.15 if client_data.ingresos_mensuales else 100000)
    
    motivo = None
    if not aprobado:
        if score < 30:
            motivo = "Puntaje muy bajo. Relación muy nueva o poca confianza."
        elif score < 45:
            motivo = "Puntaje insuficiente. Frecuencia de compra baja."
        else:
            motivo = "Puntaje cercano al mínimo requerido. Se requiere mayor historial."
    
    return CreditResult(
        aprobado=aprobado,
        monto=monto,
        puntaje=score,
        motivo=motivo
    )

def register_credit_mock(transaction: Transaction, credit_result: CreditResult) -> Dict[str, Any]:
    """
    Simula el registro del crédito en Sistecrédito
    En producción, aquí se haría la llamada real a la API
    """
    print(f"🎯 SIMULACIÓN SISTECRÉDITO:")
    print(f"   Token: {transaction.token}")
    print(f"   Cliente: {transaction.client_data.nombre} ({transaction.client_data.cedula})")
    print(f"   Puntaje: {credit_result.puntaje}/100")
    print(f"   Resultado: {'✅ APROBADO' if credit_result.aprobado else '❌ RECHAZADO'}")
    if credit_result.aprobado:
        print(f"   Monto: ${credit_result.monto:,.0f}")
    if credit_result.motivo:
        print(f"   Motivo: {credit_result.motivo}")
    print(f"   Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    return {
        "success": True,
        "transaction_id": f"SIS-{transaction.token[:8].upper()}",
        "processed_at": datetime.now().isoformat(),
        "credit_result": credit_result.dict()
    }
