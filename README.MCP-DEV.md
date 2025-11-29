# Desarrollo local: MCP mock (EPREL)

## 🚀 Inicio rápido (UN SOLO COMANDO)

Abre una terminal en la raíz del proyecto y ejecuta:

```bash
bash scripts/start-mock.sh
```

**¡Listo!** El servidor MCP mock estará disponible en http://localhost:8080

---

## 📁 ¿Qué contiene este setup?

| Archivo | Descripción |
|---------|-------------|
| `scripts/start-mock.sh` | **Ejecuta esto** - Arranca el servidor mock automáticamente |
| `scripts/setup-dev.sh` | Instala dependencias (se ejecuta automático en devcontainer) |
| `.devcontainer/devcontainer.json` | Configuración para VS Code Dev Container |
| `config/mcp-servers.json` | Lista de servidores MCP |
| `tools/mcp-mock/` | Código del servidor mock |

---

## 🧪 Probar el servidor

Una vez arrancado, puedes probar con:

```bash
curl http://localhost:8080/healthz
```

Respuesta esperada: `{"status":"ok","uptime":...}`

---

## 🔐 Notas de seguridad

- Las claves API están en variables de entorno, **no en el código**
- Para producción, configura `MCP_PROXY_API_KEY` en GitHub Secrets
- El mock usa `MCP_LOCAL_API_KEY=devkey` por defecto (solo desarrollo)
