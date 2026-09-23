# NEXUS 7.0 — Comunicação e produtividade

## Gmail

O NEXUS possui Skills para:

- listar mensagens da caixa de entrada;
- listar mensagens não lidas;
- pesquisar usando consultas do Gmail;
- ler uma mensagem por ID;
- enviar mensagens;
- responder mensagens por ID.

Enviar e responder são ações de alto risco e exigem confirmação. A leitura é de baixo risco.

## Google Tasks

O NEXUS possui uma integração separada da lista local de tarefas. As Skills `google_task_*` usam o primeiro task list retornado pela API do Google Tasks.

Comandos de exemplo:

```text
Liste minhas tarefas do Google
Adicione uma tarefa no Google Tasks estudar Python
Conclua a tarefa do Google ID
Exclua a tarefa do Google ID
```

## Lembretes

Os lembretes são locais e persistem em `data/reminders.json`. Um worker em segundo plano verifica os vencimentos. No Windows, o NEXUS tenta mostrar uma notificação toast; a fala do lembrete pode ser controlada por `REMINDER_SPEAK`.

Exemplos:

```text
Me lembre de estudar às 18:00
Me lembre de entregar o trabalho em 25/09/2026 14:00
Liste meus lembretes
Cancele o lembrete 7ac31f2b
```

## OAuth

Os tokens dos três serviços Google ficam separados:

- `data/google_token.json`
- `data/google_gmail_token.json`
- `data/google_tasks_token.json`

Isso evita alterar a autorização do Calendar quando novos escopos de Gmail ou Tasks são adicionados.
