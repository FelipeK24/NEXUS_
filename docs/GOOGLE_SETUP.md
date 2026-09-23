# Gmail + Google Calendar + Google Tasks

1. Crie ou use um projeto no Google Cloud.
2. Ative estas APIs:
   - Google Calendar API
   - Gmail API
   - Google Tasks API
3. Configure Google Auth Platform e use um cliente OAuth do tipo Desktop app. O fluxo oficial de desktop usa `InstalledAppFlow` e um servidor local temporário.
4. Baixe o JSON das credenciais e salve como `data/google_credentials.json`.
5. Execute `setup_integrations.bat`.
6. No `.env`, defina `GOOGLE_ENABLED=true`.
7. Na primeira operação de cada serviço, o Google abrirá o fluxo de autorização.

Os tokens são separados para evitar que autorizar novos escopos de Gmail/Tasks altere o token já usado pelo Calendar:

- `data/google_token.json` — Calendar
- `data/google_gmail_token.json` — Gmail
- `data/google_tasks_token.json` — Google Tasks

O Google recomenda o uso das bibliotecas oficiais e o armazenamento local do token para os quickstarts de desktop; o mesmo padrão é usado aqui.

## Gmail

O NEXUS pode:

- listar e-mails da caixa de entrada;
- listar não lidos;
- pesquisar por consultas do Gmail;
- ler uma mensagem pelo ID;
- enviar e-mail;
- responder a um e-mail pelo ID.

Enviar e responder são ações de alto risco e exigem confirmação do Security Manager.

## Google Tasks

O NEXUS pode:

- criar tarefas;
- listar tarefas pendentes;
- concluir tarefas;
- excluir tarefas.

## Lembretes locais

Lembretes não dependem do Google. São armazenados em `data/reminders.json` e o NEXUS verifica os vencidos em segundo plano. No Windows, usa uma notificação toast; opcionalmente também fala o lembrete.
