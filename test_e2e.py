#!/usr/bin/env python3
"""
Script de prueba para el flujo completo de Confianza Vecina
Simula el proceso end-to-end desde la generación del QR hasta la aprobación/rechazo
"""

import requests
import json
import time
from datetime import datetime

API_BASE_URL = "http://localhost:8000"

def test_complete_flow():
    """Prueba el flujo completo del sistema"""
    print("🧪 INICIANDO PRUEBA DE FLUJO COMPLETO")
    print("=" * 50)
    
    # Paso 1: Iniciar transacción
    print("1️⃣ Iniciando transacción...")
    response = requests.post(f"{API_BASE_URL}/transactions/initiate", json={})
    
    if response.status_code != 200:
        print(f"❌ Error al iniciar transacción: {response.status_code}")
        return False
    
    data = response.json()
    token = data["token"]
    qr_url = data["qr_url"]
    
    print(f"✅ Transacción iniciada")
    print(f"   Token: {token}")
    print(f"   QR URL: {qr_url}")
    print()
    
    # Paso 2: Simular datos del cliente desde WhatsApp
    print("2️⃣ Simulando datos del cliente desde WhatsApp...")
    client_data = {
        "token": token,
        "cedula": "12345678",
        "nombre": "Juan Pérez",
        "telefono": "3001234567",
        "direccion": "Calle 123 #45-67",
        "ingresos_mensuales": 1500000,
        "trabajo": "Empleado"
    }
    
    response = requests.post(f"{API_BASE_URL}/webhooks/whatsapp", json=client_data)
    
    if response.status_code != 200:
        print(f"❌ Error al enviar datos del cliente: {response.status_code}")
        return False
    
    print("✅ Datos del cliente enviados")
    print()
    
    # Paso 3: Simular validación del tendero desde POS
    print("3️⃣ Simulando validación del tendero desde POS...")
    store_validation = {
        "token": token,
        "cedula": "12345678",
        "nombre": "Juan Pérez",
        "tiempo_cliente": "mas-2-anos",
        "frecuencia_compra": "semanal",
        "monto_promedio": 75000,
        "confianza": 8
    }
    
    response = requests.post(f"{API_BASE_URL}/webhooks/pos", json=store_validation)
    
    if response.status_code != 200:
        print(f"❌ Error al enviar validación del tendero: {response.status_code}")
        return False
    
    print("✅ Validación del tendero enviada")
    print()
    
    # Paso 4: Consultar estado de la transacción
    print("4️⃣ Consultando estado de la transacción...")
    
    max_attempts = 10
    for attempt in range(max_attempts):
        response = requests.get(f"{API_BASE_URL}/transactions/{token}/status")
        
        if response.status_code != 200:
            print(f"❌ Error al consultar estado: {response.status_code}")
            return False
        
        data = response.json()
        status = data["status"]
        
        print(f"   Intento {attempt + 1}: Estado = {status}")
        
        if status == "completed":
            result = data["result"]
            print("✅ Transacción completada!")
            print(f"   Resultado: {json.dumps(result, indent=2, ensure_ascii=False)}")
            break
        elif status == "error":
            print(f"❌ Error en la transacción: {data.get('message', 'Sin mensaje')}")
            return False
        elif status == "expired":
            print("❌ Transacción expirada")
            return False
        
        time.sleep(2)  # Esperar 2 segundos antes del siguiente intento
    else:
        print("❌ Timeout: La transacción no se completó en el tiempo esperado")
        return False
    
    print()
    print("🎉 FLUJO COMPLETO EXITOSO!")
    return True

def test_edge_cases():
    """Prueba casos de fallo"""
    print("\n🧪 PROBANDO CASOS DE FALLO")
    print("=" * 50)
    
    # Caso 1: Token inválido
    print("1️⃣ Probando token inválido...")
    response = requests.get(f"{API_BASE_URL}/transactions/token-invalido/status")
    if response.status_code == 404:
        print("✅ Token inválido manejado correctamente")
    else:
        print(f"❌ Error inesperado: {response.status_code}")
    
    # Caso 2: Validar token expirado
    print("2️⃣ Probando validación de token...")
    response = requests.post(f"{API_BASE_URL}/transactions/validate_token", json={"token": "token-invalido"})
    if response.status_code == 200:
        data = response.json()
        if not data["valid"]:
            print("✅ Token inválido detectado correctamente")
        else:
            print("❌ Token inválido no detectado")
    
    print("✅ Casos de fallo probados")

if __name__ == "__main__":
    try:
        # Verificar que el servidor esté funcionando
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code != 200:
            print("❌ El servidor no está funcionando. Asegúrate de que esté ejecutándose en localhost:8000")
            exit(1)
        
        print("✅ Servidor funcionando correctamente")
        print()
        
        # Ejecutar pruebas
        success = test_complete_flow()
        test_edge_cases()
        
        if success:
            print("\n🎯 TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
        else:
            print("\n❌ ALGUNAS PRUEBAS FALLARON")
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor. Asegúrate de que esté ejecutándose en localhost:8000")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
