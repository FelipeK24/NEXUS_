# NEXUS — Versão Final

Assistente pessoal inteligente em Python, com voz, IA híbrida, memória persistente, planejamento, segurança, controle do PC, web, painel, tray e extensões opcionais.

## Visão

```text
Voz / Texto / Painel / API
          ↓
       Interpreter
          ↓
        Planner
          ↓
       Security
          ↓
        Pipeline
          ↓
       Dispatcher
          ↓
         Skills
          ↓
 PC / Web / Google / Vision / Smart Home (opcional)
```

## O que já funciona

- Groq como IA principal
- Qwen3 1.7B via Ollama como fallback
- Vosk para wake word
- Faster-Whisper para comandos
- detecção automática de silêncio
- Piper TTS + fallback Windows
- som da wake word
- contexto conversacional
- memória persistente e recuperação por relevância
- Planner e pipeline multi-comando
- segurança LOCK/UNLOCK e confirmações
- aplicativos e playlists do Spotify
- arquivos e processos com allowlist
- pesquisa web e navegador Playwright
- screenshot e automação web controlada (clique/preenchimento/envio)
- painel web local
- aplicativo de bandeja do Windows
- inicialização automática
- tarefas locais
- Gmail: listar, pesquisar, ler, enviar e responder
- Google Tasks: criar, listar, concluir e excluir
- lembretes locais com notificação do Windows

## Extensões opcionais

### Gmail + Calendar + Google Tasks

Implementados via OAuth de aplicativo desktop. Desativados por padrão. Gmail e Google Tasks usam tokens separados para não quebrar uma autorização de Calendar já existente.

Configuração: `docs/GOOGLE_SETUP.md`.

Detalhes de produtividade: `docs/NEXUS7_PRODUCTIVITY.md`.

### Vision

Análise de tela e imagens usando o modelo multimodal configurado em `VISION_MODEL`.

### API / Mobile

API local pronta para futuras aplicações Android/iOS e outros terminais. O app móvel em si não é incluído.

### Smart Home

Interfaces prontas para Home Assistant e ESP32. A integração fica desativada com `SMART_HOME_PROVIDER=none`.

## Primeira instalação

```bat
setup.bat
```

Depois configure `.env` com sua chave Groq.

Instale o Ollama e o fallback:

```bat
ollama pull qwen3:1.7b
```

Instale o Chromium do Playwright:

```bat
python -m playwright install chromium
```

Baixe a voz Piper configurada:

```bat
download_piper_voice.bat
```

Diagnóstico:

```bat
call .venv\Scripts\activate.bat
python doctor.py
```

## Execução

Desenvolvimento:

```bat
start_jarvis.bat
```

Segundo plano + tray:

```bat
start_background.bat
```

Painel:

```text
http://127.0.0.1:8765
```

Inicialização com Windows:

```bat
install_startup.bat
```

## Configuração principal

`.env` controla IA, voz, TTS, painel, navegador, API, visão, Google e Smart Home.

## Dados editáveis

- `data/applications.json` — aplicativos
- `data/processes.json` — processos autorizados
- `data/paths.json` — raízes de arquivos autorizadas
- `data/sites.json` — sites/aliases
- `data/spotify_playlists.json` — playlists
- `data/contacts.json` — nomes de contatos → e-mails
- `data/tasks.json` — tarefas

## Criando Skills

A regra continua:

```text
fala do usuário
→ intent
→ parameters
→ Skill
```

Veja `docs/SKILLS_GUIDE.md`.

## Segurança

O LLM interpreta, mas nunca executa código diretamente. O comando passa por validação e Security Manager antes do Dispatcher.

Ações de alto risco incluem excluir arquivos, enviar e-mail, Smart Home e apagar memória.

## Importante sobre a palavra "final"

O projeto entrega a arquitetura final planejada, mas integrações externas continuam dependentes das credenciais e equipamentos do usuário. Gmail/Calendar, Vision, Home Assistant/ESP32 e o aplicativo móvel são módulos opcionais e não ficam ativos automaticamente.

## NEXUS 7.0 — Comunicação e produtividade

Exemplos:

```text
"liste meus emails"
"procure no gmail professor"
"leia o email 18c4..."
"responda o email 18c4... dizendo vou entregar amanhã"
"liste minhas tarefas do google"
"adicione uma tarefa no google tasks estudar Python"
"me lembre de estudar as 18:00"
"liste meus lembretes"
```

Enviar/responder e-mail e ações destrutivas continuam protegidos pelo Security Manager.
