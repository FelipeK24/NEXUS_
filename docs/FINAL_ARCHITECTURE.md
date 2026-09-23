# NEXUS — Arquitetura Final

## Núcleo ativo

- Voz: Vosk + Faster-Whisper + detecção de silêncio
- TTS: Piper com fallback para pyttsx3
- IA: Groq + fallback Qwen3/Ollama
- Contexto e memória persistente
- Planner + Pipeline multi-comando
- Security Manager + LOCK/UNLOCK + confirmações
- PC Control: apps, arquivos e processos
- Web + Playwright
- Painel web local
- Windows Tray + inicialização
- Wake sound
- Tasks locais

## Extensões opcionais prontas

- Gmail + Google Calendar via OAuth
- Visão via Groq multimodal
- API local para integração com celular/outros dispositivos
- Home Assistant / ESP32
- Ponte móvel abstrata

As extensões opcionais não são ativadas por padrão. Isso evita que o primeiro boot exija credenciais externas ou dispositivos físicos.

## Segurança

O LLM nunca executa Python, shell ou chamadas de sistema diretamente. Ele apenas gera `Command`. O comando passa por validação, Security Manager, Dispatcher e Skill.

Ações de alto risco continuam exigindo confirmação. Smart Home e envio de e-mail são classificados como alto risco.

## Multi-dispositivo

A API local expõe status, lock/unlock e comandos. Para acesso pela rede local, altere `API_HOST` para `0.0.0.0`, defina `API_TOKEN` e configure regras de firewall. O celular futuro poderá usar essa API ou substituir a ponte por WebSocket.

## Visão

O módulo usa o modelo multimodal Groq configurável em `VISION_MODEL`. A configuração atual recomendada é `qwen/qwen3.6-27b`.
