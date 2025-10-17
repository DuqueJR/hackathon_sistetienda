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
    confianzaSlider: document.getElementById('confianza'),
    confianzaValue: document.getElementById('confianza-value'),
    resultadoContent: document.getElementById('resultado-content'),
    nuevoProcesoBtn: document.getElementById('nuevo-proceso-btn')
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
    elements.confianzaSlider.addEventListener('input', updateConfianzaValue);
    elements.nuevoProcesoBtn.addEventListener('click', resetearProceso);
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
            throw new Error('Error al iniciar el proceso');
        }

        const data = await response.json();
        currentToken = data.token;
        
        // Generar QR
        await generarQR(data.qr_url);
        
        // Mostrar vista QR y iniciar countdown
        showView('qr');
        iniciarCountdown(300); // 5 minutos

    } catch (error) {
        console.error('Error:', error);
        alert('Error al iniciar el proceso. Inténtalo de nuevo.');
    } finally {
        elements.iniciarBtn.disabled = false;
        elements.iniciarBtn.textContent = 'Generar QR';
    }
}

// Función para generar QR
async function generarQR(url) {
    try {
        elements.qrContainer.innerHTML = '';
        await QRCode.toCanvas(elements.qrContainer, url, {
            width: 200,
            margin: 2,
            color: {
                dark: '#000000',
                light: '#FFFFFF'
            }
        });
    } catch (error) {
        console.error('Error generando QR:', error);
        elements.qrContainer.innerHTML = '<p>Error al generar el código QR</p>';
    }
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
            cedula: formData.get('cedula'),
            nombre: formData.get('nombre'),
            tiempo_cliente: formData.get('tiempo_cliente'),
            frecuencia_compra: formData.get('frecuencia_compra'),
            monto_promedio: parseFloat(formData.get('monto_promedio')),
            confianza: parseInt(formData.get('confianza'))
        };

        const response = await fetch(`${API_BASE_URL}/webhooks/pos`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                token: currentToken,
                ...validationData
            })
        });

        if (!response.ok) {
            throw new Error('Error al validar cliente');
        }

        // Mostrar vista de resultado y empezar polling
        showView('resultado');
        clearInterval(countdownInterval);
        pollResultado();

    } catch (error) {
        console.error('Error:', error);
        alert('Error al validar cliente. Inténtalo de nuevo.');
    }
}

// Función para hacer polling del resultado
async function pollResultado() {
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/transactions/${currentToken}/status`);
            
            if (!response.ok) {
                throw new Error('Error al consultar estado');
            }

            const data = await response.json();
            
            if (data.status === 'completed') {
                clearInterval(pollInterval);
                mostrarResultado(data.result);
            } else if (data.status === 'error') {
                clearInterval(pollInterval);
                mostrarError(data.message);
            }
            
        } catch (error) {
            console.error('Error en polling:', error);
            clearInterval(pollInterval);
            mostrarError('Error al consultar el resultado');
        }
    }, 2000); // Polling cada 2 segundos
}

// Función para mostrar resultado
function mostrarResultado(resultado) {
    if (resultado.aprobado) {
        elements.resultadoContent.innerHTML = `
            <div class="resultado-aprobado">
                ✅ ¡Crédito Aprobado!
                <p>Monto: $${resultado.monto}</p>
                <p>Puntaje: ${resultado.puntaje}/100</p>
            </div>
        `;
    } else {
        elements.resultadoContent.innerHTML = `
            <div class="resultado-rechazado">
                ❌ Crédito Rechazado
                <p>Puntaje: ${resultado.puntaje}/100</p>
                <p>Motivo: ${resultado.motivo}</p>
            </div>
        `;
    }
}

// Función para mostrar error
function mostrarError(mensaje) {
    elements.resultadoContent.innerHTML = `
        <div class="resultado-rechazado">
            ❌ Error
            <p>${mensaje}</p>
        </div>
    `;
}

// Función para actualizar valor de confianza
function updateConfianzaValue() {
    elements.confianzaValue.textContent = elements.confianzaSlider.value;
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
