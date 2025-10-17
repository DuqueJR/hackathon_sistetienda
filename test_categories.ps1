# Script de pruebas para cada categoría de cliente
Write-Host "TESTS POR CATEGORIA DE CLIENTE" -ForegroundColor Magenta
Write-Host "===============================" -ForegroundColor Magenta

function Test-Category {
    param(
        [string]$CategoryName,
        [string]$Category,
        [hashtable]$ClientData,
        [hashtable]$StoreValidation,
        [string]$ExpectedCategory
    )
    
    Write-Host "`nTESTING CATEGORIA $CategoryName" -ForegroundColor Yellow
    Write-Host "===============================" -ForegroundColor Yellow
    
    try {
        # 1. Generar token
        $initiateResponse = Invoke-RestMethod -Uri "http://localhost:8000/transactions/initiate" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"store_id": "TIENDA_TEST", "tendero_name": "Tendero Test"}'
        $token = $initiateResponse.token
        Write-Host "Token: $token" -ForegroundColor Green
        
        # 2. Enviar datos del cliente
        $clientBody = @{
            token = $token
            telefono = $ClientData.telefono
            direccion = $ClientData.direccion
            ingresos_mensuales = $ClientData.ingresos_mensuales
            trabajo = $ClientData.trabajo
            psych_organized = $ClientData.psych_organized
            psych_plan = $ClientData.psych_plan
        } | ConvertTo-Json
        
        $clientResponse = Invoke-RestMethod -Uri "http://localhost:8000/webhooks/whatsapp" -Method POST -Headers @{"Content-Type"="application/json"} -Body $clientBody
        Write-Host "Cliente enviado" -ForegroundColor Green
        
        # 3. Enviar validación del tendero
        $posBody = @{
            token = $token
            cedula_cliente = $StoreValidation.cedula_cliente
            nombre_cliente = $StoreValidation.nombre_cliente
            know_buyer = $StoreValidation.know_buyer
            buy_freq = $StoreValidation.buy_freq
            avg_purchase = $StoreValidation.avg_purchase
            distance_km = $StoreValidation.distance_km
            address_verified = $StoreValidation.address_verified
        } | ConvertTo-Json
        
        $posResponse = Invoke-RestMethod -Uri "http://localhost:8000/webhooks/pos" -Method POST -Headers @{"Content-Type"="application/json"} -Body $posBody
        Write-Host "Tendero enviado" -ForegroundColor Green
        
        # 4. Consultar resultado
        Start-Sleep -Seconds 2
        $statusResponse = Invoke-RestMethod -Uri "http://localhost:8000/transactions/$token/status" -Method GET
        
        # 5. Verificar resultado
        $actualCategory = $statusResponse.result.category
        $score = $statusResponse.result.score_conf
        $cupo = $statusResponse.result.cupo_estimated
        $risk = $statusResponse.result.risk_pct
        
        Write-Host "RESULTADO:" -ForegroundColor Cyan
        Write-Host "   Categoria: $actualCategory" -ForegroundColor White
        Write-Host "   Puntaje: $([math]::Round($score, 4))" -ForegroundColor White
        Write-Host "   Cupo: $([math]::Round($cupo, 2))" -ForegroundColor White
        Write-Host "   Riesgo: $([math]::Round($risk, 2))%" -ForegroundColor White
        
        # Verificar si la categoría es correcta
        if ($actualCategory -eq $ExpectedCategory) {
            Write-Host "CATEGORIA CORRECTA: $actualCategory" -ForegroundColor Green
            return $true
        } else {
            Write-Host "CATEGORIA INCORRECTA: Esperada $ExpectedCategory, Obtenida $actualCategory" -ForegroundColor Red
            return $false
        }
        
    } catch {
        Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Datos de prueba para cada categoría
$testCases = @{}

# Categoría A - Excelente
$testCases["A"] = @{
    ClientData = @{
        telefono = "3001111111"
        direccion = "Calle 100 #10-20"
        ingresos_mensuales = 3000000
        trabajo = "Profesional"
        psych_organized = 5
        psych_plan = 5
    }
    StoreValidation = @{
        cedula_cliente = "11111111"
        nombre_cliente = "Cliente Excelente"
        know_buyer = 5
        buy_freq = 5
        avg_purchase = 150000
        distance_km = 1.0
        address_verified = $true
    }
    ExpectedCategory = "A"
}

# Categoría B - Bueno
$testCases["B"] = @{
    ClientData = @{
        telefono = "3002222222"
        direccion = "Calle 80 #15-25"
        ingresos_mensuales = 2000000
        trabajo = "Empleado"
        psych_organized = 4
        psych_plan = 4
    }
    StoreValidation = @{
        cedula_cliente = "22222222"
        nombre_cliente = "Cliente Bueno"
        know_buyer = 4
        buy_freq = 4
        avg_purchase = 100000
        distance_km = 2.0
        address_verified = $true
    }
    ExpectedCategory = "B"
}

# Categoría C - Regular
$testCases["C"] = @{
    ClientData = @{
        telefono = "3003333333"
        direccion = "Calle 50 #25-30"
        ingresos_mensuales = 1200000
        trabajo = "Empleado"
        psych_organized = 3
        psych_plan = 3
    }
    StoreValidation = @{
        cedula_cliente = "33333333"
        nombre_cliente = "Cliente Regular"
        know_buyer = 3
        buy_freq = 3
        avg_purchase = 75000
        distance_km = 3.0
        address_verified = $true
    }
    ExpectedCategory = "C"
}

# Categoría D - Riesgo
$testCases["D"] = @{
    ClientData = @{
        telefono = "3004444444"
        direccion = "Calle 30 #40-50"
        ingresos_mensuales = 900000
        trabajo = "Independiente"
        psych_organized = 2
        psych_plan = 2
    }
    StoreValidation = @{
        cedula_cliente = "44444444"
        nombre_cliente = "Cliente Riesgo"
        know_buyer = 2
        buy_freq = 2
        avg_purchase = 50000
        distance_km = 5.0
        address_verified = $false
    }
    ExpectedCategory = "D"
}

# Categoría E - Alto Riesgo
$testCases["E"] = @{
    ClientData = @{
        telefono = "3005555555"
        direccion = "Calle 20 #5-10"
        ingresos_mensuales = 600000
        trabajo = "Independiente"
        psych_organized = 1
        psych_plan = 1
    }
    StoreValidation = @{
        cedula_cliente = "55555555"
        nombre_cliente = "Cliente Alto Riesgo"
        know_buyer = 1
        buy_freq = 1
        avg_purchase = 30000
        distance_km = 10.0
        address_verified = $false
    }
    ExpectedCategory = "E"
}

# Ejecutar tests
$results = @{}
foreach ($category in $testCases.Keys) {
    $testCase = $testCases[$category]
    $result = Test-Category -CategoryName $category -Category $category -ClientData $testCase.ClientData -StoreValidation $testCase.StoreValidation -ExpectedCategory $testCase.ExpectedCategory
    $results[$category] = $result
}

# Resumen de resultados
Write-Host "`nRESUMEN DE RESULTADOS" -ForegroundColor Magenta
Write-Host "====================" -ForegroundColor Magenta

$passed = 0
$total = $results.Count

foreach ($category in $results.Keys) {
    if ($results[$category]) {
        Write-Host "Categoria $category - PASSED" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "Categoria $category - FAILED" -ForegroundColor Red
    }
}

Write-Host "`nRESULTADO FINAL: $passed/$total tests passed" -ForegroundColor $(if ($passed -eq $total) { "Green" } else { "Red" })

if ($passed -eq $total) {
    Write-Host "TODOS LOS TESTS PASARON!" -ForegroundColor Green
} else {
    Write-Host "ALGUNOS TESTS FALLARON" -ForegroundColor Red
}
