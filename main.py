from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime
from typing import Dict, Any

# Importar nuestros módulos
from models import (
    InitiateTransactionRequest, InitiateTransactionResponse,
    ValidateTokenRequest, ValidateTokenResponse,
    WhatsAppWebhookRequest, POSWebhookRequest,
    TransactionStatusResponse, TransactionStatus
)
from storage import (
    create_transaction, get_transaction, update_transaction,
    is_token_valid, calculate_credit_score, register_credit_mock
)

# Crear la aplicación FastAPI
app = FastAPI(
    title="Confianza Vecina API",
    description="Sistema de originación de crédito basado en confianza del tendero",
    version="1.0.0"
)

# Configurar CORS para permitir comunicación con frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Endpoint de bienvenida - Hola Mundo"""
    return {
        "message": "¡Hola! Confianza Vecina API está funcionando correctamente",
        "status": "active",
        "version": "1.0.0",
        "endpoints": {
            "initiate": "POST /transactions/initiate",
            "validate": "POST /transactions/validate_token",
            "whatsapp": "POST /webhooks/whatsapp",
            "pos": "POST /webhooks/pos",
            "status": "GET /transactions/{token}/status"
        }
    }

@app.get("/health")
async def health_check():
    """Endpoint para verificar el estado de la API"""
    return {"status": "healthy", "service": "confianza-vecina-api"}

@app.post("/transactions/initiate", response_model=InitiateTransactionResponse)
async def initiate_transaction(request: InitiateTransactionRequest):
    """
    Inicia una nueva transacción de crédito
    Genera un token único y URL para el QR
    """
    try:
        # Crear nueva transacción
        transaction = create_transaction(request.store_id, request.tendero_name)
        
        # Generar URL para el QR (en producción sería la URL del bot de WhatsApp)
        qr_url = f"https://wa.me/573001234567?text=Hola%20quiero%20solicitar%20credito%20token:{transaction.token}"
        
        return InitiateTransactionResponse(
            token=transaction.token,
            qr_url=qr_url,
            expires_at=transaction.expires_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al iniciar transacción: {str(e)}"
        )

@app.post("/transactions/validate_token", response_model=ValidateTokenResponse)
async def validate_token(request: ValidateTokenRequest):
    """
    Valida si un token es válido y no ha expirado
    """
    try:
        token = request.token
        valid = is_token_valid(token)
        
        if valid:
            transaction = get_transaction(token)
            return ValidateTokenResponse(
                valid=True,
                status=transaction.status,
                expires_at=transaction.expires_at
            )
        else:
            return ValidateTokenResponse(valid=False)
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al validar token: {str(e)}"
        )

@app.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: WhatsAppWebhookRequest):
    """
    Webhook para recibir datos del cliente desde WhatsApp
    """
    try:
        token = request.token
        
        # Verificar que el token existe y es válido
        if not is_token_valid(token):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token inválido o expirado"
            )
        
        # Actualizar transacción con datos del cliente
        from models import ClientData
        client_data = ClientData(
            telefono=request.telefono,
            direccion=request.direccion,
            ingresos_mensuales=request.ingresos_mensuales,
            trabajo=request.trabajo,
            psych_organized=request.psych_organized,
            psych_plan=request.psych_plan
        )
        
        update_transaction(token, client_data=client_data, status=TransactionStatus.CLIENT_DATA_RECEIVED)
        
        # Verificar si ya tenemos datos del tendero para procesar
        transaction = get_transaction(token)
        print(f"🔍 DEBUG WHATSAPP: Token {token}")
        print(f"   Estado actual: {transaction.status}")
        print(f"   Tiene client_data: {transaction.client_data is not None}")
        print(f"   Tiene store_validation: {transaction.store_validation is not None}")
        
        if transaction.store_validation:
            print(f"✅ PROCESANDO CRÉDITO: Ambos datos completos")
            # Calcular puntaje y procesar crédito
            update_transaction(token, status=TransactionStatus.PROCESSING)
            credit_result = calculate_credit_score(transaction)
            update_transaction(token, credit_result=credit_result.model_dump())
            
            # Simular registro en Sistecrédito
            register_credit_mock(transaction, credit_result)
            
            # Marcar como completado
            update_transaction(token, status=TransactionStatus.COMPLETED)
            print(f"✅ CRÉDITO COMPLETADO: Estado cambiado a COMPLETED")
        else:
            print(f"⏳ ESPERANDO DATOS DEL TENDERO: Solo datos del cliente recibidos")
        
        return {"message": "Datos del cliente recibidos correctamente", "status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar datos de WhatsApp: {str(e)}"
        )

@app.post("/webhooks/pos")
async def pos_webhook(request: POSWebhookRequest):
    """
    Webhook para recibir validación del tendero desde el POS
    """
    try:
        token = request.token
        
        # Verificar que el token existe y es válido
        if not is_token_valid(token):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token inválido o expirado"
            )
        
        # Actualizar transacción con validación del tendero
        from models import StoreValidation
        store_validation = StoreValidation(
            cedula_cliente=request.cedula_cliente,
            nombre_cliente=request.nombre_cliente,
            know_buyer=request.know_buyer,
            buy_freq=request.buy_freq,
            avg_purchase=request.avg_purchase,
            distance_km=request.distance_km,
            address_verified=request.address_verified
        )
        
        update_transaction(token, store_validation=store_validation, status=TransactionStatus.STORE_VALIDATION_RECEIVED)
        
        # Si ya tenemos datos del cliente, procesar la solicitud
        transaction = get_transaction(token)
        print(f"🔍 DEBUG POS: Token {token}")
        print(f"   Estado actual: {transaction.status}")
        print(f"   Tiene client_data: {transaction.client_data is not None}")
        print(f"   Tiene store_validation: {transaction.store_validation is not None}")
        
        if transaction.client_data:
            print(f"✅ PROCESANDO CRÉDITO: Ambos datos completos")
            # Calcular puntaje y procesar crédito
            update_transaction(token, status=TransactionStatus.PROCESSING)
            credit_result = calculate_credit_score(transaction)
            update_transaction(token, credit_result=credit_result.model_dump())
            
            # Simular registro en Sistecrédito
            register_credit_mock(transaction, credit_result)
            
            # Marcar como completado
            update_transaction(token, status=TransactionStatus.COMPLETED)
            print(f"✅ CRÉDITO COMPLETADO: Estado cambiado a COMPLETED")
        else:
            print(f"⏳ ESPERANDO DATOS DEL CLIENTE: Solo datos del tendero recibidos")
        
        return {"message": "Validación del tendero recibida correctamente", "status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar validación del POS: {str(e)}"
        )

@app.get("/transactions/{token}/status", response_model=TransactionStatusResponse)
async def get_transaction_status(token: str):
    """
    Obtiene el estado actual de una transacción
    """
    try:
        transaction = get_transaction(token)
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transacción no encontrada"
            )
        
        # Verificar si ha expirado
        if datetime.now() >= transaction.expires_at:
            update_transaction(token, status=TransactionStatus.EXPIRED)
            return TransactionStatusResponse(
                status=TransactionStatus.EXPIRED,
                message="La transacción ha expirado"
            )
        
        result = None
        if transaction.status == TransactionStatus.COMPLETED and transaction.credit_result:
            result = transaction.credit_result
        
        return TransactionStatusResponse(
            status=transaction.status,
            result=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al consultar estado: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
