# Skills do NEXUS

Consulte `docs/SKILLS_GUIDE.md` para criar e registrar novas Skills.

A pasta `extensions/` continua reservada para integrações futuras, como Smart Home e aplicativo móvel.

## NEXUS 5.0 — novas Skills

### Arquivos

```text
file_list
file_find
file_open
file_create_folder
file_move
file_delete
```

### Processos

```text
process_list
process_close
```

Configuração em:

```text
data/paths.json
data/applications.json
data/processes.json
```

Para criar uma nova Skill:

1. Crie `skills/minha_skill.py`.
2. Crie uma função que receba os parâmetros do `Command` e retorne uma string.
3. Registre a Skill em `core/dispatcher.py`.
4. Adicione a intent em `core/interpreter.py`.
5. Adicione a intent ao prompt do LLM, se necessário.
6. Defina o risco em `core/security.py` se a ação não for somente leitura.
7. Adicione testes em `tests/`.

### Exemplo

```python
from core.skill import Skill


def minha_acao(nome: str) -> str:
    return f"Olá, {nome}."

skill = Skill(
    "minha_acao",
    minha_acao,
    "Executa minha ação personalizada.",
)
```

Depois:

```python
self.registry.register(skill)
```


# NEXUS 6.0 — Web

## Web Search

Intent: `web_search`

Função: `skills/web.py::pesquisar`

Exemplo:
```text
Nexus, pesquise na internet como funciona o Ryzen 5 5500.
```

## Browser

Intents:
- `web_open`
- `browser_read`
- `browser_back`
- `browser_forward`
- `browser_refresh`
- `browser_tabs`
- `browser_close`

Essas Skills usam `core/browser.py` e Playwright.

O navegador utiliza um perfil persistente em `data/browser_profile/`. Não publique essa pasta no GitHub.
