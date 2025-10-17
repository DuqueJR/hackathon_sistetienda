# Configuración para Despliegue en Render

## Variables de Entorno
```bash
# Puerto (Render lo asigna automáticamente)
PORT=8000

# Entorno
ENVIRONMENT=production

# Configuración de CORS (ajustar según dominio)
ALLOWED_ORIGINS=https://tu-dominio.com,https://tu-frontend.com

# Configuración de WhatsApp (cuando esté listo)
WHATSAPP_TOKEN=tu_token_de_twilio
WHATSAPP_PHONE_NUMBER=+573001234567

# Configuración de Sistecrédito (cuando esté listo)
SISTECREDITO_API_URL=https://api.sistecrédito.com
SISTECREDITO_API_KEY=tu_api_key
```

## Comandos de Despliegue

### Render.com
1. **Crear nuevo Web Service**
2. **Conectar repositorio GitHub**
3. **Configurar build command**: `pip install -r requirements.txt`
4. **Configurar start command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. **Configurar variables de entorno**

### Docker (Alternativa)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Monitoreo y Logs

### Health Check
- Endpoint: `GET /health`
- Respuesta esperada: `{"status": "healthy"}`

### Logs Importantes
- Inicio de transacciones
- Errores de validación
- Resultados de crédito
- Errores de conexión

## Escalabilidad

### Horizontal Scaling
- Múltiples instancias de la aplicación
- Load balancer para distribución
- Base de datos compartida (PostgreSQL)

### Vertical Scaling
- Aumentar recursos de CPU/RAM
- Optimizar consultas de base de datos
- Cache de resultados frecuentes

## Seguridad

### Producción
- HTTPS obligatorio
- Validación de CORS estricta
- Rate limiting por IP
- Logs de auditoría
- Encriptación de datos sensibles

### Backup
- Backup automático de base de datos
- Versionado de código
- Rollback automático en caso de error
