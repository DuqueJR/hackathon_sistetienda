from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import uuid
from models import Transaction, TransactionStatus, ClientData, StoreValidation, CreditResult
from credit_heuristic import heuristic_micro_v2, get_default_config

# Almacén en memoria para las transacciones
transactions_storage: Dict[str, Transaction] = {}

def generate_token() -> str:
    """Genera un token único para la transacción"""
    return str(uuid.uuid4())

def create_transaction(store_id: str, tendero_name: str) -> Transaction:
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

def calculate_credit_score(transaction: Transaction) -> CreditResult:
    """
    Calcula el puntaje crediticio usando el modelo heurístico Micro v2
    """
    if not transaction.client_data or not transaction.store_validation:
        return CreditResult(
            category="E",
            score_conf=0.0,
            risk_pct=100.0,
            debt_capacity_pct=0.0,
            cupo_estimated=0.0,
            raw_cupo=0.0,
            comp_feature=0.0,
            comp_income=0.0,
            features={},
            clients_per_day=0,
            income_proxy_daily=0.0
        )
    
    # Preparar datos para el modelo heurístico
    client_data = transaction.client_data
    store_validation = transaction.store_validation
    
    # Crear diccionario con los datos requeridos por el modelo
    model_input = {
        "know_buyer": store_validation.know_buyer,
        "buy_freq": store_validation.buy_freq,
        "avg_purchase": store_validation.avg_purchase,
        "psych_organized": client_data.psych_organized,
        "psych_plan": client_data.psych_plan,
        "distance_km": store_validation.distance_km,
        "address_verified": store_validation.address_verified
    }
    
    try:
        # Ejecutar el modelo heurístico
        result = heuristic_micro_v2(model_input)
        
        # Convertir resultado a CreditResult
        return CreditResult(
            category=result["category"],
            score_conf=result["score_conf"],
            risk_pct=result["risk_pct"],
            debt_capacity_pct=result["debt_capacity_pct"],
            cupo_estimated=result["cupo_estimated"],
            raw_cupo=result["raw_cupo"],
            comp_feature=result["comp_feature"],
            comp_income=result["comp_income"],
            features=result["features"],
            clients_per_day=result["clients_per_day"],
            income_proxy_daily=result["income_proxy_daily"]
        )
        
    except Exception as e:
        print(f"Error en cálculo de puntaje: {e}")
        return CreditResult(
            category="E",
            score_conf=0.0,
            risk_pct=100.0,
            debt_capacity_pct=0.0,
            cupo_estimated=0.0,
            raw_cupo=0.0,
            comp_feature=0.0,
            comp_income=0.0,
            features={},
            clients_per_day=0,
            income_proxy_daily=0.0
        )

def register_credit_mock(transaction: Transaction, credit_result: CreditResult) -> Dict[str, Any]:
    """
    Simula el registro del crédito en Sistecrédito
    En producción, aquí se haría la llamada real a la API
    """
    print(f"🎯 SIMULACIÓN SISTECRÉDITO:")
    print(f"   Token: {transaction.token}")
    print(f"   Cliente: {transaction.store_validation.nombre_cliente} ({transaction.store_validation.cedula_cliente})")
    print(f"   Categoría: {credit_result.category}")
    print(f"   Puntaje: {credit_result.score_conf:.4f}")
    print(f"   Riesgo: {credit_result.risk_pct:.2f}%")
    print(f"   Cupo Estimado: ${credit_result.cupo_estimated:,.2f}")
    print(f"   Componente Feature: ${credit_result.comp_feature:,.2f}")
    print(f"   Componente Income: ${credit_result.comp_income:,.2f}")
    print(f"   Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    return {
        "success": True,
        "transaction_id": f"SIS-{transaction.token[:8].upper()}",
        "processed_at": datetime.now().isoformat(),
        "credit_result": credit_result.dict()
    }
