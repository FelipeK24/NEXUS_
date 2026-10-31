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
- `GET /api/skills` (lista intents e descrições disponíveis)
- `GET /api/history` (até 8 turnos recentes da conversa em memória)
- `GET /api/events?after_id=0&limit=50` (eventos recentes para polling)
- `POST /api/command` com `{"text":"..."}`
- `POST /api/lock`
- `POST /api/unlock`

Envie `X-NEXUS-TOKEN` em todas as requisições da API usando o valor de `API_TOKEN`.
Os corpos devem ser objetos JSON com `Content-Type: application/json`; o limite é 64 KiB e comandos podem ter até 4096 caracteres.

`API_ENABLED=true` exige `API_TOKEN`; o NEXUS não inicia a API sem essa credencial.
O painel também pode exigir um token próprio via `PANEL_TOKEN`. Sem esse token,
`PANEL_HOST` só pode apontar para loopback (`127.0.0.1`, `::1` ou `localhost`).
Quando configurado, informe `PANEL_TOKEN` no formulário exibido pelo painel.

O aplicativo móvel ainda não faz parte deste repositório; esta API é a ponte preparada para ele.

## Painel PWA para celular

O painel tambem oferece `GET /api/history` e `GET /api/skills`, protegidos pelo `PANEL_TOKEN`, para alimentar as secoes expansivas do PWA.

O PWA inclui atalhos para hora, status do PC, tarefas e downloads. Tambem permite preencher o comando a partir do historico; esses botoes apenas preenchem o campo e exigem toque em **Executar** para enviar.

No Android, use a opcao de instalar exibida pelo navegador. No iPhone/iPad, use Compartilhar > Adicionar a Tela de Inicio. O PWA fornece controle pelo navegador; um aplicativo Android/iOS nativo ainda nao esta incluido. Ao acessar pela rede local, o HTTPS tambem protege o token em transito.

Para ditar um comando, toque em **Falar**, permita o microfone e revise a transcricao antes de tocar em **Executar**. O reconhecimento depende do suporte do navegador; o processamento do audio pode usar o servico de voz fornecido pela plataforma e requer conexao com a internet em alguns navegadores. O NEXUS recebe somente o texto reconhecido quando o comando e enviado.

O painel pode ser instalado como um app web e usa a mesma origem dos endpoints do painel. Para abrir pelo celular, configure `PANEL_HOST=0.0.0.0`, defina um `PANEL_TOKEN` forte e permita a porta do painel na rede local. O token fica apenas na sessão do navegador e não é incluído no cache offline.

A instalação PWA exige contexto seguro: HTTPS na rede local ou `localhost` durante desenvolvimento. Sem HTTPS, o painel continua funcionando como página responsiva, mas o navegador pode bloquear a instalação e o service worker. O cache offline contém apenas a interface estática; status, comandos, confirmações e eventos continuam exigindo conexão com o NEXUS.

## Eventos

`/api/events` usa polling autenticado. `after_id` retorna eventos mais novos que o ID informado; `limit` aceita de 1 a 100. A resposta inclui `next_id` para continuar a paginação e `stream_id`, que muda quando o processo reinicia. O histórico guarda até 256 eventos em memória e não é persistido.

O feed registra início e fim de pipeline/comandos, duração, sucesso, intent, mudanças de modo e bloqueio. Não inclui texto bruto de comandos, respostas nem parâmetros das Skills.

### WebSocket opcional

O painel PWA pode receber o mesmo feed em tempo real. O WebSocket e opcional; desligado, o PWA continua usando o polling acima.

```env
WEBSOCKET_ENABLED=true
WEBSOCKET_HOST=127.0.0.1
WEBSOCKET_PORT=8767
```

Instale as dependencias com `pip install -r requirements.txt` e reinicie o NEXUS. Para conexao pela LAN, configure `PANEL_HOST=0.0.0.0`, um `PANEL_TOKEN` forte e `WEBSOCKET_HOST=0.0.0.0`; libere a porta 8767 na rede local. O WebSocket usa o mesmo `PANEL_TOKEN` e aceita apenas mensagens de autenticacao; comandos continuam na API HTTP protegida.

Quando o painel estiver publicado por HTTPS atraves de proxy reverso, configure `WEBSOCKET_PUBLIC_URL=wss://seu-host/caminho` e encaminhe esse caminho para `WEBSOCKET_PORT` com upgrade WebSocket habilitado. Sem proxy TLS, use o painel local; navegadores podem bloquear `ws://` em uma pagina HTTPS. O PWA tenta o WebSocket e volta ao polling se ele ficar indisponivel. O buffer de eventos continua limitado e em memoria.
