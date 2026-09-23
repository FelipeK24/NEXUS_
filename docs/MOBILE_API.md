# API para celular e outros dispositivos

Por padrão a API fica desativada e presa a `127.0.0.1`.

Para usar na LAN:

```env
API_ENABLED=true
API_HOST=0.0.0.0
API_PORT=8766
API_TOKEN=uma-chave-forte
```

Endpoints:

- `GET /api/health`
- `GET /api/status`
- `POST /api/command` com `{"text":"..."}`
- `POST /api/lock`
- `POST /api/unlock`

Envie `X-NEXUS-TOKEN` quando `API_TOKEN` estiver configurado.

O aplicativo móvel ainda não faz parte deste repositório; esta API é a ponte preparada para ele.
