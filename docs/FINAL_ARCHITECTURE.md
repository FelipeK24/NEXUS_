# NEXUS — Arquitetura Final

## Núcleo ativo

- Voz: Vosk + Faster-Whisper + detecção de silêncio
- TTS: Piper com fallback para pyttsx3
- IA: Groq + fallback Qwen3/Ollama
- Contexto e memória persistente
- Planner + Pipeline multi-comando
- Event Bus em memória para telemetria do pipeline e atualizações do painel
- Security Manager + LOCK/UNLOCK + confirmações
- PC Control: apps, arquivos e processos
- Web + Playwright
- Painel web local
- Métricas locais de CPU, RAM, disco e tráfego de rede
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

O Dispatcher confere os parâmetros contra a assinatura da Skill antes de executá-la e não repete a chamada quando ocorre um erro. Todas as instâncias do pipeline compartilham um bloqueio para que comandos vindos da voz, painel e API sejam processados em sequência. O histórico de conversa guarda tanto comandos quanto respostas das Skills.

Ações de alto risco continuam exigindo confirmação. Smart Home e envio de e-mail são classificados como alto risco.

Planos compostos são limitados a seis comandos e passam por validação integral antes da primeira Skill. Se uma etapa não puder ser interpretada ou vinculada aos parâmetros da Skill, o plano inteiro é interrompido sem executar etapas parciais.

## Multi-dispositivo

A API local expõe status, lock/unlock, comandos, Skills, histórico recente e polling de eventos. O Event Bus mantém uma janela limitada em memória e não registra o conteúdo de comandos ou respostas no feed.


## Visão

O módulo usa o modelo multimodal Groq configurável em `VISION_MODEL`. A configuração atual recomendada é `qwen/qwen3.6-27b`.

O painel pode usar um WebSocket autenticado e somente de leitura para receber eventos em tempo real. Ele e opcional e o PWA mantem o polling como fallback.
