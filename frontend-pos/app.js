// Configuración de la API
const API_BASE_URL = 'http://localhost:8000'; // Cambiar por la URL de Render en producción

// Estado de la aplicación
let currentToken = null;
let countdownInterval = null;

// Elementos del DOM
const views = {
    inicio: document.getElementById('inicio-view'),
    qr: document.getElementById('qr-view'),
    validacion: document.getElementById('validacion-view'),
    resultado: document.getElementById('resultado-view')
};

const elements = {
    iniciarBtn: document.getElementById('iniciar-btn'),
    qrContainer: document.getElementById('qr-container'),
    countdown: document.getElementById('countdown'),
    validacionForm: document.getElementById('validacion-form'),
    knowBuyerSlider: document.getElementById('know-buyer'),
    knowBuyerValue: document.getElementById('know-buyer-value'),
    buyFreqSlider: document.getElementById('buy-freq'),
    buyFreqValue: document.getElementById('buy-freq-value'),
    resultadoContent: document.getElementById('resultado-content'),
    nuevoProcesoBtn: document.getElementById('nuevo-proceso-btn'),
    irValidacionBtn: document.getElementById('ir-validacion-btn')
};

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    showView('inicio');
});

// Event Listeners
function initializeEventListeners() {
    elements.iniciarBtn.addEventListener('click', iniciarProceso);
    elements.validacionForm.addEventListener('submit', validarCliente);
    elements.knowBuyerSlider.addEventListener('input', updateKnowBuyerValue);
    elements.buyFreqSlider.addEventListener('input', updateBuyFreqValue);
    elements.nuevoProcesoBtn.addEventListener('click', resetearProceso);
    elements.irValidacionBtn.addEventListener('click', irAValidacion);
}

// Funciones de navegación
function showView(viewName) {
    Object.values(views).forEach(view => view.classList.remove('active'));
    views[viewName].classList.add('active');
}

// Función para iniciar el proceso
async function iniciarProceso() {
    try {
        elements.iniciarBtn.disabled = true;
        elements.iniciarBtn.textContent = 'Generando...';

        const response = await fetch(`${API_BASE_URL}/transactions/initiate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({})
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Error al iniciar el proceso');
        }

        const data = await response.json();
        currentToken = data.token;
        
        // Generar QR
        await generarQR(data.qr_url);
        
        // Mostrar vista QR y iniciar countdown
        showView('qr');
        iniciarCountdown(900); // 15 minutos

        // NO cambiar automáticamente a validación - el usuario debe hacer clic manualmente

    } catch (error) {
        console.error('Error:', error);
        alert(`Error al iniciar el proceso: ${error.message}`);
    } finally {
        elements.iniciarBtn.disabled = false;
        elements.iniciarBtn.textContent = 'Generar QR';
    }
}

// Función para generar QR
async function generarQR(url) {
    try {
        elements.qrContainer.innerHTML = '';
        
        // Usar qrcode-generator (librería para navegadores)
        if (typeof qrcode !== 'undefined') {
            console.log('Usando qrcode-generator');
            
            // Crear instancia de QR
            const qr = qrcode(0, 'M'); // Error correction level M
            qr.addData(url);
            qr.make();
            
            // Crear tabla HTML para mostrar el QR
            const table = document.createElement('table');
            table.style.borderCollapse = 'collapse';
            table.style.margin = '0 auto';
            table.style.border = '3px solid #e2e8f0';
            table.style.borderRadius = '10px';
            table.style.padding = '10px';
            table.style.background = 'white';
            
            const qrSize = qr.getModuleCount();
            const cellSize = Math.floor(220 / qrSize); // Ajustar tamaño
            
            for (let row = 0; row < qrSize; row++) {
                const tr = document.createElement('tr');
                for (let col = 0; col < qrSize; col++) {
                    const td = document.createElement('td');
                    td.style.width = cellSize + 'px';
                    td.style.height = cellSize + 'px';
                    td.style.backgroundColor = qr.isDark(row, col) ? '#000000' : '#FFFFFF';
                    td.style.padding = '0';
                    td.style.margin = '0';
                    tr.appendChild(td);
                }
                table.appendChild(tr);
            }
            
            elements.qrContainer.appendChild(table);
            
        } else {
            // Fallback: usar API online para generar QR
            console.log('Usando API online para generar QR');
            await generarQRConAPI(url);
        }
        
        // Agregar información adicional
        const infoDiv = document.createElement('div');
        infoDiv.style.marginTop = '10px';
        infoDiv.style.fontSize = '0.9rem';
        infoDiv.style.color = '#666';
        infoDiv.innerHTML = `
            <p><strong>Token:</strong> ${currentToken}</p>
            <p><strong>URL:</strong> ${url}</p>
        `;
        elements.qrContainer.appendChild(infoDiv);
        
    } catch (error) {
        console.error('Error generando QR:', error);
        // Mostrar fallback con enlace directo
        mostrarFallbackQR(url);
    }
}

// Función para generar QR usando API online
async function generarQRConAPI(url) {
    try {
        // Usar API de QR Server
        const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(url)}`;
        
        const img = document.createElement('img');
        img.src = qrUrl;
        img.alt = 'Código QR';
        img.style.border = '3px solid #e2e8f0';
        img.style.borderRadius = '10px';
        img.style.padding = '10px';
        img.style.background = 'white';
        
        // Verificar que la imagen se carga correctamente
        await new Promise((resolve, reject) => {
            img.onload = resolve;
            img.onerror = reject;
        });
        
        elements.qrContainer.appendChild(img);
        
    } catch (error) {
        console.error('Error con API de QR:', error);
        throw new Error('No se pudo generar el QR con ningún método');
    }
}

// Función para mostrar fallback cuando todo falla
function mostrarFallbackQR(url) {
    elements.qrContainer.innerHTML = `
        <div style="text-align: center; padding: 20px;">
            <div style="background: #f0f9ff; padding: 20px; border-radius: 10px; margin-bottom: 15px;">
                <h3 style="color: #0369a1; margin-bottom: 15px;">📱 Código QR</h3>
                <p style="color: #0369a1; margin-bottom: 15px;">
                    Para acceder al formulario de crédito, escanea este código con WhatsApp:
                </p>
                <div style="background: white; padding: 15px; border-radius: 8px; border: 2px dashed #0369a1;">
                    <p style="font-family: monospace; word-break: break-all; font-size: 0.9rem;">
                        ${url}
                    </p>
                </div>
            </div>
            <div style="background: #fef3c7; padding: 15px; border-radius: 8px;">
                <p style="margin: 0; color: #d97706; font-size: 0.9rem;">
                    <strong>Instrucciones:</strong><br>
                    1. Copia el enlace de arriba<br>
                    2. Ábrelo en WhatsApp<br>
                    3. Completa el formulario
                </p>
            </div>
        </div>
    `;
}

// Función para el countdown
function iniciarCountdown(seconds) {
    let timeLeft = seconds;
    
    function updateCountdown() {
        const minutes = Math.floor(timeLeft / 60);
        const secs = timeLeft % 60;
        elements.countdown.textContent = `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        
        if (timeLeft <= 0) {
            clearInterval(countdownInterval);
            alert('El código QR ha expirado. Por favor, genera uno nuevo.');
            resetearProceso();
            return;
        }
        
        timeLeft--;
    }
    
    updateCountdown();
    countdownInterval = setInterval(updateCountdown, 1000);
}

// Función para validar cliente
async function validarCliente(event) {
    event.preventDefault();
    
    try {
        const formData = new FormData(elements.validacionForm);
        const validationData = {
            token: currentToken,
            cedula_cliente: formData.get('cedula_cliente'),
            nombre_cliente: formData.get('nombre_cliente'),
            know_buyer: parseInt(formData.get('know_buyer')),
            buy_freq: parseInt(formData.get('buy_freq')),
            avg_purchase: parseFloat(formData.get('avg_purchase')),
            distance_km: formData.get('distance_km') ? parseFloat(formData.get('distance_km')) : null,
            address_verified: formData.get('address_verified') ? formData.get('address_verified') === 'true' : null
        };

        // Deshabilitar el formulario mientras se procesa
        const submitBtn = elements.validacionForm.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Validando...';

        const response = await fetch(`${API_BASE_URL}/webhooks/pos`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(validationData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Error al validar cliente');
        }

        const result = await response.json();
        console.log('Validación enviada:', result);

        // Mostrar vista de resultado y empezar polling
        showView('resultado');
        clearInterval(countdownInterval);
        pollResultado();

    } catch (error) {
        console.error('Error:', error);
        alert(`Error al validar cliente: ${error.message}`);
        
        // Rehabilitar el formulario en caso de error
        const submitBtn = elements.validacionForm.querySelector('button[type="submit"]');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Validar Cliente';
    }
}

// Función para hacer polling del resultado
async function pollResultado() {
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/transactions/${currentToken}/status`);
            
            if (!response.ok) {
                if (response.status === 404) {
                    clearInterval(pollInterval);
                    mostrarError('Transacción no encontrada');
                    return;
                }
                throw new Error('Error al consultar estado');
            }

            const data = await response.json();
            console.log('Estado de transacción:', data);
            
            if (data.status === 'completed') {
                clearInterval(pollInterval);
                mostrarResultado(data.result);
            } else if (data.status === 'error') {
                clearInterval(pollInterval);
                mostrarError(data.message || 'Error en el procesamiento');
            } else if (data.status === 'expired') {
                clearInterval(pollInterval);
                mostrarError('La transacción ha expirado');
            }
            
        } catch (error) {
            console.error('Error en polling:', error);
            clearInterval(pollInterval);
            mostrarError(`Error al consultar el resultado: ${error.message}`);
        }
    }, 2000); // Polling cada 2 segundos
}

// Función para mostrar resultado
function mostrarResultado(resultado) {
    const isApproved = resultado.category && ['A', 'B', 'C'].includes(resultado.category);
    
    if (isApproved) {
        elements.resultadoContent.innerHTML = `
            <div class="resultado-aprobado">
                <div style="font-size: 3rem; margin-bottom: 20px;">✅</div>
                <h3>¡Crédito Aprobado!</h3>
                <div style="margin: 20px 0;">
                    <p><strong>Categoría:</strong> ${resultado.category}</p>
                    <p><strong>Cupo estimado:</strong> $${resultado.cupo_estimated.toLocaleString('es-CO')}</p>
                    <p><strong>Puntaje de confianza:</strong> ${(resultado.score_conf * 100).toFixed(1)}%</p>
                    <p><strong>Riesgo:</strong> ${resultado.risk_pct.toFixed(1)}%</p>
                    <p><strong>Token:</strong> ${currentToken}</p>
                </div>
                <div style="background: #f0f9ff; padding: 15px; border-radius: 8px; margin-top: 20px;">
                    <p style="margin: 0; color: #0369a1;"><strong>Próximos pasos:</strong></p>
                    <p style="margin: 5px 0 0 0; color: #0369a1;">El cliente recibirá las instrucciones por WhatsApp</p>
                </div>
            </div>
        `;
    } else {
        elements.resultadoContent.innerHTML = `
            <div class="resultado-rechazado">
                <div style="font-size: 3rem; margin-bottom: 20px;">❌</div>
                <h3>Crédito Rechazado</h3>
                <div style="margin: 20px 0;">
                    <p><strong>Categoría:</strong> ${resultado.category}</p>
                    <p><strong>Puntaje de confianza:</strong> ${(resultado.score_conf * 100).toFixed(1)}%</p>
                    <p><strong>Riesgo:</strong> ${resultado.risk_pct.toFixed(1)}%</p>
                    <p><strong>Token:</strong> ${currentToken}</p>
                </div>
                <div style="background: #fef2f2; padding: 15px; border-radius: 8px; margin-top: 20px;">
                    <p style="margin: 0; color: #dc2626;"><strong>Recomendación:</strong></p>
                    <p style="margin: 5px 0 0 0; color: #dc2626;">El cliente puede intentar nuevamente en el futuro</p>
                </div>
            </div>
        `;
    }
}

// Función para mostrar error
function mostrarError(mensaje) {
    elements.resultadoContent.innerHTML = `
        <div class="resultado-rechazado">
            <div style="font-size: 3rem; margin-bottom: 20px;">⚠️</div>
            <h3>Error en el Proceso</h3>
            <div style="margin: 20px 0;">
                <p><strong>Mensaje:</strong> ${mensaje}</p>
                <p><strong>Token:</strong> ${currentToken || 'No disponible'}</p>
            </div>
            <div style="background: #fef3c7; padding: 15px; border-radius: 8px; margin-top: 20px;">
                <p style="margin: 0; color: #d97706;"><strong>Solución:</strong></p>
                <p style="margin: 5px 0 0 0; color: #d97706;">Intenta generar un nuevo proceso de crédito</p>
            </div>
        </div>
    `;
}

// Función para actualizar valor de know_buyer
function updateKnowBuyerValue() {
    elements.knowBuyerValue.textContent = elements.knowBuyerSlider.value;
}

// Función para actualizar valor de buy_freq
function updateBuyFreqValue() {
    elements.buyFreqValue.textContent = elements.buyFreqSlider.value;
}

// Función para ir a validación manualmente
function irAValidacion() {
    if (!currentToken) {
        alert('Primero debes generar un código QR');
        return;
    }
    showView('validacion');
}

// Función para resetear proceso
function resetearProceso() {
    currentToken = null;
    clearInterval(countdownInterval);
    elements.validacionForm.reset();
    elements.confianzaValue.textContent = '5';
    elements.resultadoContent.innerHTML = '<div class="loading">Procesando solicitud...</div>';
    showView('inicio');
}
