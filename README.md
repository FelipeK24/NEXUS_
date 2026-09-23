# NEXUS

> **NEXUS** is a personal AI assistant developed in Python, featuring voice interaction, artificial intelligence, persistent memory, computer control, productivity integrations, and a futuristic interface.

**Current version:** `7.0`
**Next major version:** `8.0`
**Primary platform:** Windows
**Primary language:** Portuguese (Brazil)

---

# 🇧🇷 Português

## 🧠 Sobre o projeto

O **NEXUS** é um assistente pessoal inteligente desenvolvido em Python.

O projeto foi inspirado em conceitos de assistentes como JARVIS, mas possui uma arquitetura própria, modular e expansível.

O objetivo é criar um sistema capaz de:

* ouvir comandos;
* compreender linguagem natural;
* executar ações;
* controlar o computador;
* armazenar e recuperar memórias;
* utilizar serviços externos;
* responder por voz;
* interagir através de uma interface visual;
* funcionar continuamente em segundo plano;
* futuramente controlar outros dispositivos.

A prioridade do projeto é manter uma arquitetura **modular, segura e extensível**.

---

## ⚙️ Arquitetura

O fluxo principal do NEXUS:

```text
                 ┌─────────────────┐
                 │     USUÁRIO     │
                 └────────┬────────┘
                          │
                    voz / texto
                          │
                          ▼
                 ┌─────────────────┐
                 │    LISTENER     │
                 │ Vosk / Whisper  │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │   INTERPRETER   │
                 │ Regras + LLM    │
                 └────────┬────────┘
                          │
                     Command
                          │
                          ▼
                 ┌─────────────────┐
                 │    DISPATCHER   │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │     SKILLS      │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │     SPEAKER     │
                 │ Piper / Windows │
                 └─────────────────┘
```

O LLM **não executa comandos diretamente**.

Ele interpreta a solicitação do usuário e produz uma estrutura de comando. A execução passa por validação, segurança, Dispatcher e Skills.

---

## 🤖 Inteligência Artificial

### Groq

O Groq pode ser utilizado como provedor principal de IA.

```env
GROQ_API_KEY=sua_chave
```

A chave deve permanecer no `.env`.

### Ollama

O NEXUS também possui suporte para modelos locais através do Ollama.

Modelo utilizado durante o desenvolvimento:

```text
Qwen3 1.7B
```

Arquitetura:

```text
NEXUS
  │
  ├── Groq
  │
  └── Ollama
       └── Qwen3 1.7B
```

---

## 🎙️ Sistema de voz

O sistema de voz utiliza diferentes etapas:

```text
Microfone
   ↓
Vosk
   ↓
Wake Word: "Nexus"
   ↓
faster-whisper
   ↓
Interpreter
   ↓
Command
   ↓
Skills
   ↓
Piper
   ↓
Resposta de voz
```

### Wake Word

O NEXUS pode permanecer aguardando pela palavra:

```text
"Nexus"
```

Quando detectada, o reconhecimento completo do comando é iniciado.

### Speech-to-Text

O reconhecimento de comandos utiliza:

```text
faster-whisper
```

### Text-to-Speech

O sistema utiliza:

```text
Piper
```

com suporte adicional a recursos de voz do Windows.

---

## 🧠 Memória

O NEXUS possui memória persistente.

As informações são armazenadas localmente em:

```text
data/memory.json
```

O sistema suporta:

* armazenamento;
* recuperação;
* busca por relevância;
* atualização;
* esquecimento;
* limpeza;
* persistência entre reinicializações.

Exemplos:

```text
"lembre que meu violão é..."
```

```text
"você lembra do meu projeto?"
```

```text
"esqueça essa informação"
```

---

## 💬 Contexto

Além da memória permanente, o NEXUS mantém contexto temporário da conversa.

Isso permite comandos dependentes das interações anteriores.

Exemplo:

```text
Usuário:
Abra o Spotify.

NEXUS:
Spotify aberto.

Usuário:
Agora abra minha playlist de treino.
```

---

## 🧩 Skills

O NEXUS utiliza uma arquitetura baseada em Skills.

Exemplos:

```text
time
calculator
open_application
close_application
open_spotify_playlist
system_info
system_control
remember
forget
recall_memory
clear_memory
clear_context
```

Novas habilidades podem ser adicionadas sem modificar todo o núcleo do sistema.

---

## 🖥️ Controle do computador

O NEXUS possui recursos para:

* abrir aplicações;
* fechar aplicações;
* consultar informações do sistema;
* controlar funções do Windows;
* trabalhar com processos;
* controlar volume;
* executar ações no computador;
* abrir playlists do Spotify.

---

## 🎵 Spotify

O NEXUS possui integração para abertura de playlists do Spotify.

Exemplo:

```text
"Nexus, abra o Spotify."
```

ou:

```text
"Nexus, abra minha playlist de treino."
```

---

## 📅 Produtividade

O sistema possui integrações com serviços do Google.

Atualmente fazem parte da arquitetura:

* Google Calendar;
* Gmail;
* Google Tasks;
* lembretes;
* tarefas;
* notificações.

A autenticação utiliza OAuth.

Tokens são armazenados separadamente:

```text
data/
├── google_token.json
├── google_gmail_token.json
└── google_tasks_token.json
```

Esses arquivos **não devem ser enviados para o GitHub**.

---

## 🔐 Segurança

O NEXUS possui níveis de segurança:

```text
LOW
MEDIUM
HIGH
```

Também possui estados:

```text
LOCK
UNLOCK
```

Ações sensíveis podem exigir confirmação.

### Princípio de segurança

```text
Usuário
   ↓
LLM
   ↓
Command estruturado
   ↓
Validação
   ↓
Segurança
   ↓
Dispatcher
   ↓
Skill
   ↓
Sistema
```

O modelo de IA não deve possuir acesso direto ao sistema operacional.

---

## 🖥️ Interface

O NEXUS possui uma interface visual futurista.

Elementos principais:

* Orb central;
* informações de hardware;
* histórico de interações;
* controles;
* status do sistema;
* animações;
* estética azul/roxa.

### Estados do Orb

| Estado   | Cor              |
| -------- | ---------------- |
| Offline  | Cinza            |
| Online   | `#007CC4`        |
| Thinking | Amarelo queimado |
| Speaking | Roxo             |

Durante a fala, o Orb aumenta sua movimentação e intensidade.

---

## 📊 Monitoramento

A interface pode mostrar:

```text
CPU
RAM
GPU
DISK
```

Também existe uma área dedicada às interações recentes.

---

## 🌐 API

Uma das próximas etapas é transformar o NEXUS em um Core acessível por vários dispositivos.

Arquitetura planejada:

```text
                    NEXUS CORE
                        │
                        ▼
                       API
              ┌─────────┼─────────┐
              │         │         │
              ▼         ▼         ▼
             PC      Celular   Notebook
```

Endpoints planejados:

```text
POST /api/command
GET  /api/status
GET  /api/skills
GET  /api/memory
GET  /api/history
POST /api/lock
POST /api/unlock
```

A API utiliza autenticação por token.

---

## 📱 NEXUS Mobile

Existe também um projeto de aplicativo mobile.

A ideia é transformar o celular em um cliente do NEXUS Core:

```text
Celular
   │
   │ HTTP
   ▼
NEXUS API
   │
   ▼
NEXUS CORE
```

O aplicativo possui como objetivo:

* Dashboard;
* status do NEXUS;
* LOCK / UNLOCK;
* envio de comandos;
* histórico;
* configurações da API;
* autenticação;
* respostas por voz.

A entrada de voz pelo celular ainda é uma etapa futura.

---

## 📁 Estrutura

```text
NEXUS/
│
├── core/
│   ├── dispatcher.py
│   ├── interpreter.py
│   ├── listener.py
│   ├── speaker.py
│   ├── llm.py
│   ├── skill.py
│   ├── skill_registry.py
│   ├── context.py
│   ├── memory.py
│   └── ...
│
├── skills/
│   ├── time.py
│   ├── calculator.py
│   ├── applications.py
│   ├── system.py
│   ├── system_control.py
│   ├── memory.py
│   └── ...
│
├── data/
│   ├── memory.json
│   └── ...
│
├── panel/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── scripts/
│   └── ...
│
├── tests/
│   └── ...
│
├── main.py
├── requirements.txt
├── .env
└── README.md
```

---

## 🚀 Instalação

### 1. Clone o repositório

```bat
git clone https://github.com/FelipeK24/NEXUS.git
cd NEXUS
```

### 2. Crie o ambiente virtual

```bat
python -m venv .venv
```

### 3. Ative o ambiente

```bat
.venv\Scripts\activate
```

### 4. Instale as dependências

```bat
pip install -r requirements.txt
```

### 5. Configure o `.env`

```env
GROQ_API_KEY=sua_chave

API_ENABLED=false
API_HOST=127.0.0.1
API_PORT=8766
API_TOKEN=sua-chave-forte
```

### 6. Execute

```bat
python main.py
```

---

## 🧪 Testes

Durante o desenvolvimento foram utilizados testes independentes para os principais componentes:

```text
test.py
test_llm.py
test_stt.py
test_whisper.py
test_silence.py
```

A intenção é validar componentes individualmente antes de integrá-los ao sistema principal.

---

## 📈 Evolução

### NEXUS 1.x

* arquitetura inicial;
* comandos;
* Skills;
* Dispatcher.

### NEXUS 2.x

* integração com LLM;
* Ollama;
* interpretação natural.

### NEXUS 3.x

* memória;
* contexto;
* persistência.

### NEXUS 4.x

* Vosk;
* Wake Word;
* Whisper;
* TTS.

### NEXUS 5.x

* controle do computador;
* aplicações;
* processos;
* Spotify.

### NEXUS 6.x

* Google Calendar;
* Gmail;
* Google Tasks;
* OAuth;
* produtividade.

### NEXUS 7.0

* consolidação da arquitetura;
* segurança;
* múltiplas Skills;
* memória;
* voz;
* painel;
* produtividade;
* integrações externas;
* preparação para multi-device.

---

## 🚧 NEXUS 8.0

A versão 8.0 representa a próxima grande evolução arquitetural.

O objetivo é transformar o NEXUS de um assistente executado em um único computador em um **Core acessível por múltiplos dispositivos**.

```text
                 NEXUS CORE
                     │
             ┌───────┴───────┐
             │      API      │
             └───────┬───────┘
                     │
       ┌─────────────┼─────────────┐
       │             │             │
       ▼             ▼             ▼
      PC          Celular       Notebook
```

Planejamento:

* REST API;
* autenticação;
* gerenciamento de dispositivos;
* WebSocket;
* eventos em tempo real;
* painel conectado ao Core;
* comunicação LAN;
* múltiplos clientes;
* permissões por dispositivo.

---

## 🔮 Futuro

Possíveis funcionalidades futuras:

### 🏠 Smart Home

* Home Assistant;
* ESP32;
* Arduino;
* sensores;
* iluminação;
* tomadas;
* automação residencial.

### 💻 Multi-device

* PC principal;
* notebook Acer;
* celular;
* terminais adicionais.

### 🎙️ Voice Terminals

Um computador secundário poderá funcionar como terminal de voz:

```text
Microfone
   ↓
Wake Word
   ↓
NEXUS Core
   ↓
Resposta
   ↓
Alto-falante
```

### 🧠 Inteligência avançada

* planejamento;
* agentes especializados;
* memória avançada;
* visão computacional;
* análise de tela;
* automação de navegador;
* workflows complexos.

---

## 🎯 Filosofia

O NEXUS não pretende ser apenas um chatbot com voz.

A visão do projeto é criar um **sistema operacional pessoal inteligente**:

```text
             ┌───────────────┐
             │      IA       │
             └───────┬───────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
      Memória       Voz         Visão
        │            │            │
        └────────────┼────────────┘
                     ▼
                 NEXUS CORE
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
      PC          Internet       Devices
```

---

## 📌 Status atual

| Sistema              | Status |
| -------------------- | ------ |
| Modular Architecture | ✅      |
| Skill Registry       | ✅      |
| Dispatcher           | ✅      |
| Interpreter          | ✅      |
| Groq                 | ✅      |
| Ollama               | ✅      |
| Qwen3                | ✅      |
| Persistent Memory    | ✅      |
| Conversation Context | ✅      |
| Vosk                 | ✅      |
| Wake Word            | ✅      |
| faster-whisper       | ✅      |
| Piper                | ✅      |
| PC Control           | ✅      |
| Spotify              | ✅      |
| Google Calendar      | ✅      |
| Gmail                | ✅      |
| Google Tasks         | ✅      |
| OAuth                | ✅      |
| Security / Lock      | ✅      |
| Futuristic Panel     | ✅      |
| Core API             | 🚧     |
| Multi-device         | 🚧     |
| WebSocket            | 🚧     |
| NEXUS Mobile         | 🚧     |
| Smart Home           | 🔮     |
| Acer Voice Terminal  | 🔮     |

---

# 🇺🇸 English

## 🧠 About

**NEXUS** is a personal AI assistant built with Python.

The project was inspired by assistants such as JARVIS, but uses its own modular and extensible architecture.

The goal is to create a system capable of:

* listening to voice commands;
* understanding natural language;
* executing actions;
* controlling the computer;
* storing and retrieving memories;
* using external services;
* responding through speech;
* providing a visual interface;
* running continuously in the background;
* eventually controlling other devices.

The project focuses on **modularity, security, and extensibility**.

---

## ⚙️ Architecture

The main NEXUS pipeline is:

```text
                 ┌─────────────────┐
                 │      USER       │
                 └────────┬────────┘
                          │
                    voice / text
                          │
                          ▼
                 ┌─────────────────┐
                 │    LISTENER     │
                 │ Vosk / Whisper  │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │   INTERPRETER   │
                 │ Rules + LLM     │
                 └────────┬────────┘
                          │
                     Command
                          │
                          ▼
                 ┌─────────────────┐
                 │    DISPATCHER   │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │     SKILLS      │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │     SPEAKER     │
                 │ Piper / Windows │
                 └─────────────────┘
```

The LLM **does not directly execute system commands**.

It interprets the user's request and produces a structured command. Execution then goes through validation, security, the Dispatcher, and the appropriate Skill.

---

## 🤖 Artificial Intelligence

### Groq

Groq can be used as the primary AI provider.

```env
GROQ_API_KEY=your_api_key
```

### Ollama

NEXUS also supports local AI through Ollama.

Development model:

```text
Qwen3 1.7B
```

Architecture:

```text
NEXUS
  │
  ├── Groq
  │
  └── Ollama
       └── Qwen3 1.7B
```

---

## 🎙️ Voice System

The voice pipeline is:

```text
Microphone
   ↓
Vosk
   ↓
Wake Word: "Nexus"
   ↓
faster-whisper
   ↓
Interpreter
   ↓
Command
   ↓
Skills
   ↓
Piper
   ↓
Voice response
```

### Wake Word

NEXUS can remain in a listening state waiting for:

```text
"Nexus"
```

After detection, full command recognition begins.

### Speech-to-Text

Commands are transcribed using:

```text
faster-whisper
```

### Text-to-Speech

The project uses:

```text
Piper
```

with Windows voice support as an additional fallback.

---

## 🧠 Memory

NEXUS includes persistent memory.

Memory is stored locally in:

```text
data/memory.json
```

Supported operations include:

* storing information;
* retrieving information;
* relevance-based search;
* updating information;
* forgetting information;
* clearing memory;
* persistence across restarts.

---

## 💬 Conversation Context

NEXUS also maintains temporary conversation context.

This allows commands to depend on previous interactions.

Example:

```text
User:
Open Spotify.

NEXUS:
Spotify opened.

User:
Now open my training playlist.
```

---

## 🧩 Skills

NEXUS uses a modular Skill architecture.

Examples include:

```text
time
calculator
open_application
close_application
open_spotify_playlist
system_info
system_control
remember
forget
recall_memory
clear_memory
clear_context
```

New capabilities can be added without rewriting the entire core.

---

## 🖥️ Computer Control

NEXUS can interact with Windows to:

* open applications;
* close applications;
* inspect system information;
* control system functions;
* work with processes;
* control volume;
* perform computer actions;
* open Spotify playlists.

---

## 🎵 Spotify

NEXUS includes Spotify playlist launching support.

Example:

```text
"Nexus, open Spotify."
```

or:

```text
"Nexus, open my training playlist."
```

---

## 📅 Productivity

The project includes integrations with Google services:

* Google Calendar;
* Gmail;
* Google Tasks;
* reminders;
* tasks;
* notifications.

OAuth is used for authentication.

Tokens are stored separately:

```text
data/
├── google_token.json
├── google_gmail_token.json
└── google_tasks_token.json
```

These files must **never be committed to GitHub**.

---

## 🔐 Security

NEXUS uses security levels:

```text
LOW
MEDIUM
HIGH
```

It also provides:

```text
LOCK
UNLOCK
```

Sensitive actions may require confirmation.

### Security principle

```text
User
 ↓
LLM
 ↓
Structured Command
 ↓
Validation
 ↓
Security
 ↓
Dispatcher
 ↓
Skill
 ↓
System
```

The AI model should never have unrestricted direct access to the operating system.

---

## 🖥️ Interface

NEXUS includes a futuristic visual interface.

Main elements:

* central Orb;
* hardware information;
* interaction history;
* controls;
* system status;
* animations;
* blue/purple visual theme.

### Orb states

| State    | Color        |
| -------- | ------------ |
| Offline  | Gray         |
| Online   | `#007CC4`    |
| Thinking | Burnt yellow |
| Speaking | Purple       |

The Orb becomes more animated while NEXUS is speaking.

---

## 🌐 API

The next architectural step is turning NEXUS into a Core accessible from multiple devices.

Planned architecture:

```text
                    NEXUS CORE
                        │
                        ▼
                       API
              ┌─────────┼─────────┐
              │         │         │
              ▼         ▼         ▼
             PC      Mobile     Notebook
```

Planned endpoints:

```text
POST /api/command
GET  /api/status
GET  /api/skills
GET  /api/memory
GET  /api/history
POST /api/lock
POST /api/unlock
```

The API uses token-based authentication.

---

## 📱 NEXUS Mobile

A separate mobile application is also part of the project.

The goal is to make the smartphone a client of the NEXUS Core:

```text
Mobile
   │
   │ HTTP
   ▼
NEXUS API
   │
   ▼
NEXUS CORE
```

Planned features include:

* Dashboard;
* NEXUS status;
* LOCK / UNLOCK;
* command sending;
* conversation history;
* API configuration;
* authentication;
* voice responses.

Mobile voice input is planned for a future stage.

---

## 🚧 NEXUS 8.0

NEXUS 8.0 is planned as the next major architectural evolution.

The goal is to transform NEXUS from a single-computer assistant into a **multi-device AI Core**.

```text
                 NEXUS CORE
                     │
             ┌───────┴───────┐
             │      API      │
             └───────┬───────┘
                     │
       ┌─────────────┼─────────────┐
       │             │             │
       ▼             ▼             ▼
      PC          Mobile       Notebook
```

Planned features:

* REST API;
* authentication;
* device management;
* WebSocket;
* real-time events;
* Core-connected interface;
* LAN communication;
* multiple clients;
* per-device permissions.

---

## 🔮 Future

Possible future capabilities:

### Smart Home

* Home Assistant;
* ESP32;
* Arduino;
* sensors;
* lighting;
* smart plugs;
* home automation.

### Multi-device

* main PC;
* Acer notebook;
* smartphone;
* additional terminals.

### Voice Terminals

A secondary computer could act as a dedicated voice terminal:

```text
Microphone
   ↓
Wake Word
   ↓
NEXUS Core
   ↓
Response
   ↓
Speaker
```

### Advanced Intelligence

Future possibilities include:

* task planning;
* specialized agents;
* advanced memory;
* computer vision;
* screen analysis;
* browser automation;
* complex workflows.

---

## 🎯 Philosophy

NEXUS is not intended to be just a voice chatbot.

The long-term vision is to create a **personal intelligent operating system**:

```text
             ┌───────────────┐
             │      AI       │
             └───────┬───────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
      Memory        Voice        Vision
        │            │            │
        └────────────┼────────────┘
                     ▼
                 NEXUS CORE
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
      PC          Internet       Devices
```

Each component has a specific responsibility and can be replaced or expanded without rebuilding the entire system.

---

## 📌 Current Status

| System               | Status |
| -------------------- | ------ |
| Modular Architecture | ✅      |
| Skill Registry       | ✅      |
| Dispatcher           | ✅      |
| Interpreter          | ✅      |
| Groq                 | ✅      |
| Ollama               | ✅      |
| Qwen3                | ✅      |
| Persistent Memory    | ✅      |
| Conversation Context | ✅      |
| Vosk                 | ✅      |
| Wake Word            | ✅      |
| faster-whisper       | ✅      |
| Piper                | ✅      |
| PC Control           | ✅      |
| Spotify              | ✅      |
| Google Calendar      | ✅      |
| Gmail                | ✅      |
| Google Tasks         | ✅      |
| OAuth                | ✅      |
| Security / Lock      | ✅      |
| Futuristic Panel     | ✅      |
| Core API             | 🚧     |
| Multi-device         | 🚧     |
| WebSocket            | 🚧     |
| NEXUS Mobile         | 🚧     |
| Smart Home           | 🔮     |
| Acer Voice Terminal  | 🔮     |

---

## 👨‍💻 Development

NEXUS is a personal project developed by **Felipe**.

The project is continuously evolving as new systems and integrations are implemented.

The main development principles are:

* modularity;
* security;
* extensibility;
* testability;
* maintainability;
* multi-device readiness.

---

## 📜 License

A project license has not been defined yet.

Until a license is added to the repository, the code should be considered **All Rights Reserved**.

---

# NEXUS

> **One Core. Multiple Devices. One Assistant.**

```text
NEXUS
Personal AI System
Version 7.0
```
