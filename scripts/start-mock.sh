#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Script para arrancar el servidor MCP mock en un solo comando
# Uso: bash scripts/start-mock.sh
# =============================================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MOCK_DIR="$ROOT_DIR/tools/mcp-mock"

echo "🚀 Iniciando MCP Mock Server para EPREL..."

# Verificar Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js no está instalado. Instálalo primero (v18+)."
    exit 1
fi

# Ir al directorio del mock
cd "$MOCK_DIR"

# Instalar dependencias si no existen
if [ ! -d "node_modules" ]; then
    echo "📦 Instalando dependencias..."
    npm install
fi

# Crear directorio de logs
mkdir -p "$ROOT_DIR/logs"

# Configurar variables por defecto para desarrollo local
export MCP_LOCAL_API_KEY="${MCP_LOCAL_API_KEY:-devkey}"
export LOG_LEVEL="${LOG_LEVEL:-debug}"
export PORT="${PORT:-8080}"

echo ""
echo "✅ Servidor MCP Mock listo!"
echo "   URL: http://localhost:$PORT"
echo "   Health: http://localhost:$PORT/healthz"
echo "   API Key: $MCP_LOCAL_API_KEY"
echo ""
echo "   Endpoints disponibles:"
echo "   - POST /v1/chat/completions"
echo "   - POST /v1/completions"
echo ""
echo "   Presiona Ctrl+C para detener el servidor."
echo ""

# Arrancar el servidor
node server.js
