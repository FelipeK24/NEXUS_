# Gmail + Google Calendar

1. Crie um projeto no Google Cloud.
2. Ative Gmail API e Google Calendar API.
3. Configure OAuth para um aplicativo Desktop.
4. Baixe o JSON de credenciais e salve como `data/google_credentials.json`.
5. Execute `setup_integrations.bat`.
6. No `.env`, defina `GOOGLE_ENABLED=true`.
7. Execute o NEXUS e faça a autorização quando a primeira operação Google for usada.

O token é salvo em `data/google_token.json` e não deve ser enviado ao GitHub.
