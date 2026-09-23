# Como adicionar novas Skills ao NEXUS

O NEXUS separa interpretação e execução.

A forma recomendada é:

```text
Frase do usuário
    ↓
Interpreter
    ↓
Command
    ↓
Security
    ↓
Dispatcher
    ↓
Skill
```

## 1. Crie a Skill

Crie um arquivo em `skills/`.

Exemplo:

```python
import webbrowser


def abrir_playlist(nome: str) -> str:
    playlists = {
        "treino": "https://open.spotify.com/playlist/SEU_ID",
        "calma": "https://open.spotify.com/playlist/OUTRO_ID",
    }

    chave = nome.strip().lower()
    url = playlists.get(chave)

    if not url:
        return f"Não encontrei a playlist {nome}."

    webbrowser.open(url)
    return f"Abrindo a playlist {nome}."
```

## 2. Registre a Skill

No `core/dispatcher.py`:

```python
from skills import minha_skill
```

E dentro de `_register_skills()`:

```python
self.registry.register(
    Skill(
        "abrir_playlist",
        minha_skill.abrir_playlist,
        "Abre uma playlist.",
    )
)
```

## 3. Permita a intent

No `core/interpreter.py`, adicione:

```python
"abrir_playlist",
```

ao conjunto `ALLOWED_INTENTS`.

## 4. Crie um detector local

Para comandos previsíveis, prefira uma regra local antes do LLM:

```python
def _detect_abrir_playlist(text: str) -> Command | None:
    prefixes = (
        "abra a playlist ",
        "abrir a playlist ",
        "abra o spotify na playlist ",
        "abra o spotify em ",
    )

    for prefix in prefixes:
        if text.startswith(prefix):
            nome = text[len(prefix):].strip()
            if nome:
                return _command("abrir_playlist", text, nome=nome)

    return None
```

Depois coloque `_detect_abrir_playlist` na tupla `detectors` de `interpretar()`.

## 5. Segurança

Se a Skill fizer algo sensível, adicione a intent ao `risk_level()` em `core/security.py`.

Exemplo:

```python
if command.intent == "minha_skill_perigosa":
    return "high"
```

Assim o NEXUS pode exigir LOCK/UNLOCK e confirmação.

## Regra prática

Uma Skill deve fazer uma coisa bem definida.

Exemplos:

```text
abrir spotify
abrir playlist
fechar spotify
pesquisar youtube
criar pasta
enviar email
consultar calendario
```

Evite colocar dezenas de funções diferentes dentro de uma única Skill.


## Playlist sem mexer no Python

Para o exemplo do Spotify, você pode simplesmente editar:

```text
data/spotify_playlists.json
```

Exemplo:

```json
{
    "treino": "https://open.spotify.com/playlist/SEU_ID",
    "calma": "https://open.spotify.com/playlist/OUTRO_ID",
    "igreja": "https://open.spotify.com/playlist/OUTRO_ID"
}
```

Depois diga:

```text
Abra o Spotify na playlist igreja
```

Para uma nova função mais complexa, aí sim normalmente você cria uma nova Skill e registra uma nova intent.
