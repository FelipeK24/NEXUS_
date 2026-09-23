# NEXUS 6.0 — Web e navegador

O NEXUS 6.0 adiciona acesso controlado à internet e automação básica de navegador.

## Skills

- `web_search`: pesquisa na internet e retorna título, URL e snippet.
- `web_open`: abre um site ou URL no navegador controlado pelo NEXUS.
- `browser_read`: lê o texto visível da página atual.
- `browser_back`: volta uma página.
- `browser_forward`: avança uma página.
- `browser_refresh`: atualiza a página.
- `browser_tabs`: lista as abas abertas no navegador do NEXUS.
- `browser_close`: encerra o navegador controlado pelo NEXUS.

## Exemplos de comandos

```text
Nexus, pesquise na internet placas de vídeo usadas.
Nexus, pesquise Python classes.
Nexus, abra o site GitHub.
Nexus, abra https://example.com
Nexus, leia a página atual.
Nexus, volte no navegador.
Nexus, avance no navegador.
Nexus, atualize a página.
Nexus, quais abas estão abertas?
Nexus, feche o navegador.
```

## Sites nomeados

Os atalhos ficam em:

```text
data/sites.json
```

É possível adicionar novos aliases:

```json
{
    "escola": "https://exemplo.com",
    "meu projeto": "https://github.com/..."
}
```

## Perfil do navegador

O navegador usa um perfil separado em:

```text
data/browser_profile/
```

Esse diretório não deve ser enviado ao GitHub. Ele pode armazenar cookies e sessões do navegador.

## Playwright

O NEXUS usa Playwright para controlar o navegador. O Playwright recomenda instalar a biblioteca e os binários do navegador com:

```bat
pip install playwright
playwright install chromium
```

A implementação do NEXUS usa uma thread dedicada para o Playwright, evitando que comandos vindos do painel e da voz disputem o mesmo objeto do navegador.

## Configuração

No `.env`:

```env
WEB_SEARCH_ENGINE=bing
WEB_SEARCH_LIMIT=6
WEB_REQUEST_TIMEOUT=10
BROWSER_HEADLESS=false
BROWSER_CHANNEL=
BROWSER_PROFILE_DIR=data/browser_profile
BROWSER_NAV_TIMEOUT=15000
BROWSER_READ_LIMIT=8000
```

`BROWSER_HEADLESS=false` significa que o navegador aparece na tela quando o NEXUS o utiliza.

Para executar o NEXUS sem abrir o navegador visualmente:

```env
BROWSER_HEADLESS=true
```

O NEXUS 6.0 ainda não realiza cliques, preenchimento de formulários, login, compras ou envio de informações. Essas ações ficam para uma fase futura e deverão passar por confirmações de segurança mais fortes.


## Automação web controlada

As Skills `browser_click`, `browser_type` e `web_action` podem interagir com elementos por seletor. Clique e preenchimento são risco médio; envio/ações finais são risco alto. O NEXUS deve estar em `UNLOCK` para prosseguir e solicitará confirmação conforme o nível de risco.
