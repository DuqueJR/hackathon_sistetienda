#!/usr/bin/env python3
"""
Script de prueba para el flujo completo de Confianza Vecina con nuevo modelo Micro v2
Simula el proceso end-to-end desde la generación del QR hasta la aprobación/rechazo
"""

import requests
import json
import time
from datetime import datetime

API_BASE_URL = "http://localhost:8000"

def test_complete_flow():
    """Prueba el flujo completo del sistema con nuevo modelo"""
    print("🧪 INICIANDO PRUEBA DE FLUJO COMPLETO - MODELO MICRO V2")
    print("=" * 60)
    
    # Paso 1: Iniciar transacción
    print("1️⃣ Iniciando transacción...")
    initiate_data = {
        "store_id": "TIENDA_001",
        "tendero_name": "María González"
    }
    response = requests.post(f"{API_BASE_URL}/transactions/initiate", json=initiate_data)
    
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
    
    # Paso 2: Simular datos del cliente desde WhatsApp (nuevo modelo)
    print("2️⃣ Simulando datos del cliente desde WhatsApp...")
    client_data = {
        "token": token,
        "telefono": "3001234567",
        "direccion": "Calle 123 #45-67",
        "ingresos_mensuales": 1500000,
        "trabajo": "Empleado",
        "psych_organized": 4,  # Cliente organizado
        "psych_plan": 3         # Planificación moderada
    }
    
    response = requests.post(f"{API_BASE_URL}/webhooks/whatsapp", json=client_data)
    
    if response.status_code != 200:
        print(f"❌ Error al enviar datos del cliente: {response.status_code}")
        print(f"   Respuesta: {response.text}")
        return False
    
    print("✅ Datos del cliente enviados")
    print()
    
    # Paso 3: Simular validación del tendero desde POS (nuevo modelo)
    print("3️⃣ Simulando validación del tendero desde POS...")
    store_validation = {
        "token": token,
        "cedula_cliente": "12345678",
        "nombre_cliente": "Juan Pérez",
        "know_buyer": 4,        # Conoce al cliente hace tiempo
        "buy_freq": 3,          # Compra semanalmente
        "avg_purchase": 75000,   # Monto promedio alto
        "distance_km": 2.5,     # Cerca de la tienda
        "address_verified": True # Dirección verificada
    }
    
    response = requests.post(f"{API_BASE_URL}/webhooks/pos", json=store_validation)
    
    if response.status_code != 200:
        print(f"❌ Error al enviar validación del tendero: {response.status_code}")
        print(f"   Respuesta: {response.text}")
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
            
            # Validar que el resultado tenga la estructura del nuevo modelo
            if "category" in result and "score_conf" in result and "cupo_estimated" in result:
                print(f"✅ Modelo Micro v2 funcionando correctamente")
                print(f"   Categoría: {result['category']}")
                print(f"   Puntaje: {result['score_conf']:.4f}")
                print(f"   Cupo: ${result['cupo_estimated']:,.2f}")
                print(f"   Riesgo: {result['risk_pct']:.2f}%")
            else:
                print("❌ Estructura del resultado incorrecta")
                return False
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
    print("🎉 FLUJO COMPLETO EXITOSO CON MODELO MICRO V2!")
    return True

def test_different_categories():
    """Prueba diferentes categorías del modelo"""
    print("\n🧪 PROBANDO DIFERENTES CATEGORÍAS")
    print("=" * 50)
    
    test_cases = [
        {
            "name": "Cliente Categoría A (Excelente)",
            "client": {"psych_organized": 5, "psych_plan": 5},
            "store": {"know_buyer": 5, "buy_freq": 5, "avg_purchase": 150000, "distance_km": 1.0, "address_verified": True}
        },
        {
            "name": "Cliente Categoría C (Regular)",
            "client": {"psych_organized": 3, "psych_plan": 3},
            "store": {"know_buyer": 3, "buy_freq": 2, "avg_purchase": 50000, "distance_km": 5.0, "address_verified": False}
        },
        {
            "name": "Cliente Categoría E (Riesgo)",
            "client": {"psych_organized": 1, "psych_plan": 1},
            "store": {"know_buyer": 1, "buy_freq": 1, "avg_purchase": 10000, "distance_km": 50.0, "address_verified": False}
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"{i}️⃣ Probando: {case['name']}")
        
        # Iniciar transacción
        initiate_data = {"store_id": f"TIENDA_{i:03d}", "tendero_name": f"Tendero {i}"}
        response = requests.post(f"{API_BASE_URL}/transactions/initiate", json=initiate_data)
        
        if response.status_code != 200:
            print(f"❌ Error al iniciar transacción: {response.status_code}")
            continue
        
        token = response.json()["token"]
        
        # Enviar datos del cliente
        client_data = {
            "token": token,
            "telefono": f"300123456{i}",
            "direccion": f"Calle {i} #45-67",
            "ingresos_mensuales": 1000000 + (i * 500000),
            "trabajo": f"Trabajo {i}",
            **case["client"]
        }
        
        response = requests.post(f"{API_BASE_URL}/webhooks/whatsapp", json=client_data)
        if response.status_code != 200:
            print(f"❌ Error al enviar datos del cliente: {response.status_code}")
            continue
        
        # Enviar validación del tendero
        store_validation = {
            "token": token,
            "cedula_cliente": f"1234567{i}",
            "nombre_cliente": f"Cliente {i}",
            **case["store"]
        }
        
        response = requests.post(f"{API_BASE_URL}/webhooks/pos", json=store_validation)
        if response.status_code != 200:
            print(f"❌ Error al enviar validación: {response.status_code}")
            continue
        
        # Esperar resultado
        time.sleep(3)
        response = requests.get(f"{API_BASE_URL}/transactions/{token}/status")
        
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "completed" and "result" in data:
                result = data["result"]
                print(f"✅ {case['name']}: Categoría {result['category']}, Cupo ${result['cupo_estimated']:,.2f}")
            else:
                print(f"❌ {case['name']}: Estado {data['status']}")
        else:
            print(f"❌ {case['name']}: Error {response.status_code}")
        
        print()

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
    
    # Caso 3: Datos incompletos
    print("3️⃣ Probando datos incompletos...")
    response = requests.post(f"{API_BASE_URL}/webhooks/whatsapp", json={
        "token": "token-test",
        "telefono": "3001234567",
        "psych_organized": 3,
        "psych_plan": 3
    })
    if response.status_code == 400:
        print("✅ Datos incompletos manejados correctamente")
    else:
        print(f"❌ Error inesperado: {response.status_code}")
    
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
        test_different_categories()
        test_edge_cases()
        
        if success:
            print("\n🎯 TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
            print("🚀 El nuevo modelo Micro v2 está funcionando correctamente!")
        else:
            print("\n❌ ALGUNAS PRUEBAS FALLARON")
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor. Asegúrate de que esté ejecutándose en localhost:8000")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
