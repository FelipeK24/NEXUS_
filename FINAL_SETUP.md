# NEXUS FINAL — instalação

1. Instale Python 3.11.
2. Instale Ollama e execute `ollama pull qwen3:1.7b`.
3. Execute `setup.bat`.
4. Abra `.env` e preencha `GROQ_API_KEY`.
5. Rode `python doctor.py`.
6. Para desenvolvimento: `start_jarvis.bat`.
7. Para uso normal: `start_background.bat`.
8. Para painel: `start_with_panel.bat`.
9. Para inicialização automática: `install_startup.bat`.
10. Para Gmail/Calendar: `setup_integrations.bat` e siga `docs/GOOGLE_SETUP.md`.

## Recursos opcionais

- Vision: `VISION_ENABLED=true` + Groq API.
- API móvel/LAN: `API_ENABLED=true`, `API_HOST=0.0.0.0`, `API_TOKEN=<chave forte>`.
- Smart Home: defina `SMART_HOME_PROVIDER=homeassistant` ou `esp32` e configure as variáveis correspondentes.

## Segurança

Não envie `.env`, tokens Google, credenciais, perfil do navegador ou chaves de Smart Home ao GitHub.
