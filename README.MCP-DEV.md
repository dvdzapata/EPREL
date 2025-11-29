# Desarrollo local: MCP mock y configuración de devcontainer (EPREL)

Estos archivos y scripts te permiten levantar un entorno local y un servidor MCP de prueba para desarrollo y pruebas con Copilot Coding Agent.

Contenido:
- .devcontainer/devcontainer.json — configuración del contenedor de desarrollo (VS Code).
- .github/copilot-coding-agent.json — plantilla JSON para configurar servidores MCP en la coding agent.
- config/mcp-servers.json — lista local de servidores MCP.
- tools/mcp-mock/* — mock de servidor MCP (Node.js) con logging, control de concurrencia y timeouts.

Rápido inicio (local, sin devcontainer):
1. Ir al mock:
   cd tools/mcp-mock
2. Instalar:
   npm install
3. Arrancar (en la terminal verás logging detallado y procesos):
   MCP_LOCAL_API_KEY=devkey LOG_LEVEL=debug npm start
   - El servidor quedará escuchando en http://localhost:8080
   - Endpoints: POST /v1/chat/completions y POST /v1/completions
   - Health: GET /healthz

Notas de seguridad y configuración:
- Para uso real, no comites las claves. Define variables de entorno en el CI o en GitHub Secrets (ej. MCP_PROXY_API_KEY).
- En .github/copilot-coding-agent.json los campos apiKeyEnv indican el nombre de la variable de entorno que debe contener la clave.
- Los timeouts, concurrencia y rate-limits son parámetros de ejemplo; ajústalos a tus necesidades.

Integración con Dev Container:
- El devcontainer ya exporta `MCP_SERVERS_CONFIG=/workspace/config/mcp-servers.json`.
- Dentro del container puedes arrancar el mock o tus servicios reales.
- `postCreateCommand` ejecuta `scripts/setup-dev.sh` si existe; puedes añadir instalaciones específicas ahí.

Siguientes pasos que puedo hacer por ti:
- Puedo abrir un PR en el repo con estos archivos ya añadidos.
- Puedo añadir un script `scripts/setup-dev.sh` para instalar dependencias automáticas en el container.
- Puedo crear una versión del mock que haga proxy a OpenAI (sin mandar claves públicas), con reintentos y reanudación de descargas/streams si lo necesitas.

Dime si quieres que cree el PR con estos archivos y que añada el script `scripts/setup-dev.sh` y la acción de GitHub para arrancar/validar el MCP mock automáticamente.
