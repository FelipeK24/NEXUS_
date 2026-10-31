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
- monitoramento local de CPU, RAM, disco e tráfego de rede
- feed de atividade ao vivo no painel via Event Bus local
- aplicativo de bandeja do Windows
- inicialização automática
- tarefas locais

## Extensões opcionais

### Gmail + Calendar

Implementados via OAuth de aplicativo desktop. Desativados por padrão.

Configuração: `docs/GOOGLE_SETUP.md`.

### Vision

Análise de tela e imagens usando o modelo multimodal configurado em `VISION_MODEL`.

### API / Mobile

Inclui endpoints autenticados para Skills, histórico recente e polling de eventos, além de painel web instalável como PWA em celulares.


### Smart Home

Interfaces prontas para Home Assistant e ESP32. A integração fica desativada com `SMART_HOME_PROVIDER=none`.

## Primeira instalação

```bat
setup.bat
```

Depois configure `.env` com sua chave Groq.

O modelo definido em `WHISPER_MODEL` precisa estar disponível localmente antes de usar a voz. O NEXUS não baixa modelos Whisper automaticamente; configure `WHISPER_MODEL` para uma pasta local ou prepare o cache manualmente.

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

## Testes

Instale a dependência de desenvolvimento e execute a suíte:

```bat
python -m pip install -r requirements-dev.txt
python -m pytest -q
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
