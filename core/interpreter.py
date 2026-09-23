from __future__ import annotations

import json
import logging
import re
import unicodedata
from typing import Any

from core.command import Command
from core.config import ASSISTANT_NAME
from core.context import ConversationContext
from core.llm import llm

logger = logging.getLogger("jarvis.interpreter")
_context = ConversationContext(max_turns=8)

ALLOWED_INTENTS = {
    "time",
    "calculator",
    "open_application",
    "open_spotify_playlist",
    "close_application",
    "system_info",
    "system_control",
    "clear_context",
    "general_question",
    "remember",
    "forget",
    "recall_memory",
    "clear_memory",
    "file_list",
    "file_find",
    "file_open",
    "file_create_folder",
    "file_move",
    "file_delete",
    "process_list",
    "process_close",
    "web_search",
    "web_open",
    "browser_read",
    "browser_back",
    "browser_forward",
    "browser_refresh",
    "browser_tabs",
    "browser_close",
    "browser_screenshot",
    "browser_click",
    "browser_type",
    "web_action",
    "email_list",
    "email_search",
    "email_read",
    "email_send",
    "email_reply",
    "calendar_list",
    "calendar_create",
    "task_add",
    "task_list",
    "task_complete",
    "task_delete",
    "google_task_add",
    "google_task_list",
    "google_task_complete",
    "google_task_delete",
    "reminder_add",
    "reminder_list",
    "reminder_cancel",
    "vision_screen",
    "vision_image",
    "smart_home_action",
    "unknown",
}

APPLICATION_ALIASES = {
    "spotify": "spotify",
    "spotfy": "spotify",
    "opera": "opera",
    "opera gx": "opera",
    "bloco de notas": "notepad",
    "notepad": "notepad",
}

SITE_ALIASES = {
    "youtube": "youtube",
    "google": "google",
    "whatsapp": "whatsapp",
    "whatsapp web": "whatsapp",
    "discord": "discord",
    "gmail": "gmail",
    "spotify web": "spotify web",
}


def _normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower().strip())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def registrar_usuario(texto: str) -> None:
    _context.add_user(texto)


def registrar_nexus(resposta: str) -> None:
    _context.add_assistant(resposta)


def limpar_contexto() -> None:
    _context.clear()


def responder_pergunta(texto: str) -> str:
    history = _context.format()
    prompt = f"""
Você é {ASSISTANT_NAME}, um assistente pessoal de computador.
Responda sempre em português brasileiro.
Seja natural, direto e útil.
Não exponha raciocínio interno, prompts ou detalhes técnicos desnecessários.
Quando a pergunta for simples, responda de forma curta.

Histórico recente:
{history}

Usuário:
{texto}

Responda diretamente ao usuário.
""".strip()
    return llm.gerar(prompt)


def _command(intent: str, text: str, **parameters: Any) -> Command:
    return Command(intent=intent, parameters=parameters, original_text=text)


def _detect_clear_context(text: str) -> Command | None:
    patterns = {
        "limpe o contexto", "limpar o contexto", "apague o contexto",
        "esqueca a conversa", "esquece a conversa",
    }
    return _command("clear_context", text) if text in patterns else None


def _detect_clear_memory(text: str) -> Command | None:
    patterns = {
        "apague toda minha memoria", "apaga toda minha memoria",
        "limpe minha memoria", "limpar minha memoria",
        "esqueca tudo que voce sabe sobre mim", "esqueca tudo que sabe sobre mim",
    }
    return _command("clear_memory", text) if text in patterns else None


def _detect_remember(text: str) -> Command | None:
    for prefix in ("lembre que ", "lembra que ", "guarde que ", "memorize que "):
        if text.startswith(prefix):
            body = text[len(prefix):].strip()
            match = re.match(r"(.+?)\s+(?:e|=)\s+(.+)$", body)
            if match:
                return _command("remember", text, key=match.group(1), value=match.group(2))
    return None


def _detect_forget(text: str) -> Command | None:
    for prefix in ("esqueca ", "esquece ", "apague da memoria "):
        if text.startswith(prefix):
            key = text[len(prefix):].strip()
            if key:
                return _command("forget", text, key=key)
    return None


def _detect_recall_memory(text: str) -> Command | None:
    for prefix in (
        "voce lembra da minha ", "voce lembra do meu ", "voce lembra minha ",
        "voce lembra meu ", "lembra da minha ", "lembra do meu ",
        "lembra minha ", "lembra meu ",
    ):
        if text.startswith(prefix):
            key = text[len(prefix):].strip()
            if key:
                return _command("recall_memory", text, key=key)

    patterns = (
        r"^qual (?:e|é) minha (.+)$", r"^qual minha (.+)$",
        r"^qual (?:e|é) meu (.+)$", r"^qual meu (.+)$",
        r"^qual (?:e|é) a minha (.+)$", r"^qual a minha (.+)$",
        r"^qual (?:e|é) o meu (.+)$", r"^qual o meu (.+)$",
    )
    for pattern in patterns:
        match = re.match(pattern, text)
        if match:
            key = match.group(1).strip()
            if key not in {"nome", "idade", "hora", "dia", "data"}:
                return _command("recall_memory", text, key=key)

    if text.startswith(("voce lembra qual ", "voce lembra onde ", "voce lembra quando ", "lembra qual ", "lembra onde ", "lembra quando ")):
        return _command("recall_memory", text, key=text)
    return None


def _detect_time(text: str) -> Command | None:
    patterns = {"que horas sao", "me diga a hora", "qual a hora", "qual e a hora"}
    return _command("time", text) if text in patterns else None


def _detect_calculator(text: str) -> Command | None:
    expression = text
    for prefix in ("calcule ", "quanto e ", "quanto da ", "quanto é ", "quanto dá "):
        if text.startswith(prefix):
            expression = text[len(prefix):]
            break
    if not any(char.isdigit() for char in expression):
        return None
    if not re.search(r"[+\-*/%]|\bmais\b|\bmenos\b|\bvezes\b|\bdividido\b", expression):
        return None
    return _command("calculator", text, expression=expression.rstrip("?").strip())


def _detect_spotify_playlist(text: str) -> Command | None:
    prefixes = (
        "abra o spotify na playlist ", "abrir o spotify na playlist ",
        "abra o spotify em ", "abrir o spotify em ",
        "abre o spotify na playlist ", "abre o spotify em ",
        "abra a playlist ", "abrir a playlist ", "abre a playlist ",
    )
    for prefix in prefixes:
        if text.startswith(prefix):
            name = text[len(prefix):].strip()
            if name:
                return _command("open_spotify_playlist", text, nome=name)
    return None


def _detect_close_application(text: str) -> Command | None:
    for prefix in ("feche ", "fechar ", "encerre ", "encerra "):
        if text.startswith(prefix):
            raw_app = text[len(prefix):].strip()
            raw_app = re.sub(r"^(?:o|a)\s+", "", raw_app)
            app = APPLICATION_ALIASES.get(raw_app, raw_app)
            if app:
                return _command("close_application", text, application=app)
    return None


def _detect_open_application(text: str) -> Command | None:
    for prefix in ("abra ", "abrir ", "execute ", "executar ", "inicie "):
        if text.startswith(prefix):
            target = text[len(prefix):].strip()
            target = re.sub(r"^(?:o|a)\s+", "", target)
            target = APPLICATION_ALIASES.get(target, target)
            if target in set(APPLICATION_ALIASES.values()):
                return _command("open_application", text, application=target)
            site = SITE_ALIASES.get(target)
            if site:
                return _command("web_open", text, target=site)
    return None


def _detect_system_info(text: str) -> Command | None:
    return _command("system_info", text) if text in {
        "informacoes do sistema", "status do sistema", "como esta o pc", "status do computador"
    } else None


def _detect_web_search(text: str) -> Command | None:
    prefixes = (
        "pesquise na internet ",
        "pesquise na web ",
        "procure na internet ",
        "procure na web ",
        "busque na internet ",
        "busque na web ",
        "pesquise ",
        "pesquisa ",
    )
    for prefix in prefixes:
        if text.startswith(prefix):
            query = text[len(prefix):].strip()
            if query:
                return _command("web_search", text, query=query)
    return None


def _detect_web_browser(text: str) -> Command | None:
    for prefix in (
        "abra o site ", "abrir o site ", "abre o site ",
        "abra a pagina ", "abrir a pagina ", "abre a pagina ",
        "abra a página ", "abrir a página ", "abre a página ",
        "abra https://", "abrir https://", "abre https://",
        "abra http://", "abrir http://", "abre http://",
    ):
        if text.startswith(prefix):
            target = text[len(prefix):].strip()
            if prefix.endswith("https://"):
                target = "https://" + target
            elif prefix.endswith("http://"):
                target = "http://" + target
            if target:
                return _command("web_open", text, target=target)

    if text in {
        "leia a pagina", "leia a página", "leia o site",
        "resuma a pagina", "resuma a página",
        "leia a pagina atual", "leia a página atual",
    }:
        return _command("browser_read", text)

    if text in {
        "volte no navegador", "volta no navegador", "volte uma pagina",
        "volte uma página", "pagina anterior", "página anterior",
    }:
        return _command("browser_back", text)

    if text in {
        "avance no navegador", "avanca no navegador", "avança no navegador",
        "avance uma pagina", "avance uma página", "pagina seguinte",
        "página seguinte",
    }:
        return _command("browser_forward", text)

    if text in {
        "atualize o navegador", "atualiza o navegador",
        "atualize a pagina", "atualize a página",
        "recarregue a pagina", "recarregue a página",
    }:
        return _command("browser_refresh", text)

    if text in {
        "quais abas estao abertas", "quais abas estão abertas",
        "liste as abas", "mostre as abas",
    }:
        return _command("browser_tabs", text)

    if text in {
        "feche o navegador", "fecha o navegador",
        "encerrar navegador", "encerre o navegador",
    }:
        return _command("browser_close", text)

    return None




def _detect_browser_actions(text: str) -> Command | None:
    if text in {"tire um print da pagina", "tire um screenshot da pagina", "tire um print da página", "tire um screenshot da página"}:
        return _command("browser_screenshot", text, path="data/browser_screenshot.png")
    if text.startswith("clique no elemento "):
        selector=text[len("clique no elemento "):].strip()
        if selector:
            return _command("browser_click", text, selector=selector)
    if text.startswith("preencha o campo ") and " com " in text:
        selector, value = text[len("preencha o campo "):].split(" com ",1)
        if selector.strip() and value.strip():
            return _command("browser_type", text, selector=selector.strip(), content=value.strip())
    if text.startswith("envie o formulario pelo elemento ") or text.startswith("envie o formulário pelo elemento "):
        prefix = "envie o formulario pelo elemento " if text.startswith("envie o formulario pelo elemento ") else "envie o formulário pelo elemento "
        selector=text[len(prefix):].strip()
        if selector:
            return _command("web_action", text, action="submit", selector=selector)
    return None


def _detect_email_calendar_tasks(text: str) -> Command | None:
    # Gmail
    if text in {
        "liste meus emails",
        "mostre meus emails",
        "liste meus e mails",
        "mostre meus e mails",
        "quais emails eu tenho",
        "quais emails novos eu tenho",
        "quais sao meus emails novos",
    }:
        query = "in:inbox is:unread" if "novos" in text else "in:inbox"
        return _command("email_list", text, query=query)

    for prefix in (
        "procure no gmail ",
        "pesquise no gmail ",
        "procure emails sobre ",
        "pesquise emails sobre ",
    ):
        if text.startswith(prefix):
            query = text[len(prefix):].strip()
            if query:
                return _command("email_search", text, query=query)

    for prefix in ("leia o email ", "leia o e-mail ", "abra o email ", "abra o e-mail "):
        if text.startswith(prefix):
            identifier = text[len(prefix):].strip()
            if identifier:
                return _command("email_read", text, identifier=identifier)

    if text.startswith(("responda o email ", "responda o e-mail ")) and " dizendo " in text:
        prefix = "responda o email " if text.startswith("responda o email ") else "responda o e-mail "
        identifier, body = text[len(prefix):].split(" dizendo ", 1)
        if identifier.strip() and body.strip():
            return _command("email_reply", text, message_id=identifier.strip(), body=body.strip())

    if text.startswith(("envie um email para ", "envia um email para ", "mande um email para ", "mandar um email para ")):
        rest = text.split(" para ", 1)[1].strip()
        match = re.match(r"(.+?)\s+assunto\s+(.+?)\s+mensagem\s+(.+)$", rest)
        if match:
            return _command(
                "email_send",
                text,
                to=match.group(1).strip(),
                subject=match.group(2).strip(),
                body=match.group(3).strip(),
            )

    # Calendar
    if text in {"mostre minha agenda", "liste minha agenda", "quais eventos eu tenho", "o que tenho na agenda", "me mostre minha agenda", "consulte minha agenda"}:
        return _command("calendar_list", text, days=7)
    if text.startswith(("agende ", "crie um evento ", "marque ")):
        match = re.match(r"^(?:agende|crie um evento|marque) (.+?) em (.+?) ate (.+)$", text)
        if match:
            return _command("calendar_create", text, summary=match.group(1).strip(), start=match.group(2).strip(), end=match.group(3).strip())

    # Google Tasks
    if text.startswith(("adicione uma tarefa no google tasks ", "adicione uma tarefa no google ", "crie uma tarefa no google tasks ")):
        if text.startswith("adicione uma tarefa no google tasks "):
            prefix = "adicione uma tarefa no google tasks "
        elif text.startswith("crie uma tarefa no google tasks "):
            prefix = "crie uma tarefa no google tasks "
        else:
            prefix = "adicione uma tarefa no google "
        title = text[len(prefix):].strip()
        if title:
            return _command("google_task_add", text, title=title)
    if text in {"liste minhas tarefas do google", "mostre minhas tarefas do google", "liste minhas tarefas do google tasks"}:
        return _command("google_task_list", text)
    for prefix in ("conclua a tarefa do google ", "conclua a tarefa no google "):
        if text.startswith(prefix):
            return _command("google_task_complete", text, identifier=text[len(prefix):].strip())
    for prefix in ("exclua a tarefa do google ", "apague a tarefa do google "):
        if text.startswith(prefix):
            return _command("google_task_delete", text, identifier=text[len(prefix):].strip())

    # Local tasks
    if text.startswith(("adicione uma tarefa ", "crie uma tarefa ", "anote uma tarefa ")):
        title = re.sub(r"^(?:adicione uma tarefa|crie uma tarefa|anote uma tarefa) ", "", text).strip()
        if title:
            return _command("task_add", text, title=title)
    if text in {"liste minhas tarefas", "quais sao minhas tarefas", "mostre minhas tarefas"}:
        return _command("task_list", text)
    for prefix in ("conclua a tarefa ", "marque a tarefa como concluida "):
        if text.startswith(prefix):
            return _command("task_complete", text, identifier=text[len(prefix):].strip())
    for prefix in ("exclua a tarefa ", "apague a tarefa "):
        if text.startswith(prefix):
            return _command("task_delete", text, identifier=text[len(prefix):].strip())

    # Reminders
    if text in {"liste meus lembretes", "mostre meus lembretes", "quais sao meus lembretes"}:
        return _command("reminder_list", text)
    for prefix in ("cancele o lembrete ", "cancele um lembrete ", "apague o lembrete "):
        if text.startswith(prefix):
            identifier = text[len(prefix):].strip()
            if identifier:
                return _command("reminder_cancel", text, identifier=identifier)
    match = re.match(r"^me lembre de (.+?) (?:as|às) (.+)$", text)
    if match:
        message = match.group(1).strip()
        when = "hoje às " + match.group(2).strip()
        return _command("reminder_add", text, message=message, when=when)
    match = re.match(r"^me lembre de (.+?) em (.+)$", text)
    if match:
        message = match.group(1).strip()
        when = match.group(2).strip()
        return _command("reminder_add", text, message=message, when=when)
    match = re.match(r"^(?:crie|adicione) (?:um )?lembrete(?: de)? (.+?) para (.+)$", text)
    if match:
        return _command("reminder_add", text, message=match.group(1).strip(), when=match.group(2).strip())
    match = re.match(r"^me lembre (.+?) as (.+)$", text)
    if match:
        return _command("reminder_add", text, message=match.group(1).strip(), when="hoje às " + match.group(2).strip())

    if text in {"analise minha tela", "analise a minha tela", "o que tem na minha tela", "o que aparece na minha tela", "leia minha tela"}:
        return _command("vision_screen", text, question="Descreva o que aparece na minha tela e destaque o que for relevante.")
    for prefix in ("analise a imagem ", "analise a imagem em ", "leia a imagem "):
        if text.startswith(prefix):
            path = text[len(prefix):].strip()
            if path:
                return _command("vision_image", text, path=path, question="Descreva a imagem e responda de forma útil ao usuário.")
    if text.startswith(("acenda ", "apague a luz ", "ligue ", "desligue ")):
        return _command("smart_home_action", text, device=text, action="user_request", parameters={"command": text})
    return None

def _detect_system_control(text: str) -> Command | None:
    if text in {"aumente o volume", "aumentar o volume", "volume para cima"}:
        return _command("system_control", text, action="volume_up")
    if text in {"diminua o volume", "diminuir o volume", "volume para baixo"}:
        return _command("system_control", text, action="volume_down")
    if text in {"mute", "mudo", "ative o mudo", "desative o mudo"}:
        return _command("system_control", text, action="volume_mute")
    for prefix in ("google ",):
        if text.startswith(prefix):
            query = text[len(prefix):].strip()
            if query:
                return _command("system_control", text, action="google_search", query=query)
    for prefix in ("procure no youtube ", "youtube "):
        if text.startswith(prefix):
            query = text[len(prefix):].strip()
            if query:
                return _command("system_control", text, action="youtube_search", query=query)
    return None


def _detect_file_list(text: str) -> Command | None:
    patterns = (
        r"^(?:liste|listar|mostre|mostrar|veja|ver) (?:os )?(?:arquivos|conteudo|conteúdo) (?:de|da|do) (.+)$",
        r"^(?:liste|listar|mostre|mostrar) (?:os )?arquivos(?: da| de| do)?(?: pasta)? (.+)$",
    )
    for pattern in patterns:
        m = re.match(pattern, text)
        if m:
            return _command("file_list", text, path=m.group(1).strip())
    if text in {"liste meus downloads", "mostre meus downloads", "liste os downloads"}:
        return _command("file_list", text, path="downloads")
    return None


def _detect_file_find(text: str) -> Command | None:
    patterns = (
        r"^(?:encontre|encontrar|ache|achar|procure|procurar) (?:o )?(?:arquivo )?(.+?)(?: na pasta (.+))?$",
        r"^(?:busque|buscar) (?:por )?(?:um )?arquivo (.+?)(?: em (.+))?$",
    )
    for pattern in patterns:
        m = re.match(pattern, text)
        if m:
            query = m.group(1).strip()
            path = (m.group(2) or "").strip()
            if query:
                return _command("file_find", text, query=query, path=path)
    return None


def _detect_file_open(text: str) -> Command | None:
    for prefix in ("abra o arquivo ", "abrir o arquivo ", "abra arquivo ", "abrir arquivo "):
        if text.startswith(prefix):
            path = text[len(prefix):].strip()
            if path:
                return _command("file_open", text, path=path)
    return None


def _detect_file_create_folder(text: str) -> Command | None:
    patterns = (
        r"^(?:crie|criar|abra) (?:uma )?pasta chamada (.+?)(?: em (.+))?$",
        r"^(?:crie|criar) (?:uma )?pasta (.+?)(?: em (.+))?$",
    )
    for pattern in patterns:
        m = re.match(pattern, text)
        if m:
            name = m.group(1).strip()
            base = (m.group(2) or "desktop").strip()
            path = f"{base}/{name}"
            return _command("file_create_folder", text, path=path)
    return None


def _detect_file_move(text: str) -> Command | None:
    patterns = (
        r"^(?:mova|mover) (.+?) (?:para|pra) (.+)$",
        r"^(?:transfira|transferir) (.+?) (?:para|pra) (.+)$",
    )
    for pattern in patterns:
        m = re.match(pattern, text)
        if m:
            return _command("file_move", text, source=m.group(1).strip(), destination=m.group(2).strip())
    return None


def _detect_file_delete(text: str) -> Command | None:
    for prefix in ("apague o arquivo ", "exclua o arquivo ", "delete o arquivo ", "remova o arquivo "):
        if text.startswith(prefix):
            path = text[len(prefix):].strip()
            if path:
                return _command("file_delete", text, path=path)
    return None


def _detect_processes(text: str) -> Command | None:
    if text in {
        "quais processos estao abertos", "quais processos estão abertos",
        "quais processos estao rodando", "quais processos estão rodando",
        "quais programas estao rodando", "quais programas estão rodando",
        "mostre os processos", "liste os processos",
    }:
        return _command("process_list", text)

    for prefix in ("feche o processo ", "encerre o processo ", "fechar processo "):
        if text.startswith(prefix):
            name = text[len(prefix):].strip()
            if name:
                return _command("process_close", text, process_name=name)
    return None


def _validate_command(command: Command) -> Command:
    if command.intent not in ALLOWED_INTENTS:
        return _command("unknown", command.original_text)

    if command.intent in {"open_application", "close_application"}:
        application = str(command.parameters.get("application", "")).strip().lower()
        if not application:
            return _command("unknown", command.original_text)
        return Command(command.intent, {"application": APPLICATION_ALIASES.get(application, application)}, command.original_text)

    if command.intent == "open_spotify_playlist":
        nome = str(command.parameters.get("nome", "")).strip()
        return command if nome else _command("unknown", command.original_text)

    string_params = {
        "file_list": ("path",),
        "file_find": ("query", "path"),
        "file_open": ("path",),
        "file_create_folder": ("path",),
        "file_move": ("source", "destination"),
        "file_delete": ("path",),
        "process_close": ("process_name",),
        "web_search": ("query",),
        "web_open": ("target",),
        "browser_screenshot": ("path",),
        "browser_click": ("selector",),
        "browser_type": ("selector", "content"),
        "web_action": ("action", "selector"),
        "email_search": ("query",),
        "email_read": ("identifier",),
        "email_reply": ("message_id", "body"),
    }
    if command.intent in string_params:
        cleaned: dict[str, str] = {}
        for key in string_params[command.intent]:
            value = str(command.parameters.get(key, "")).strip()
            if key in {"path", "query", "source", "destination", "process_name"} and key != "path":
                pass
            cleaned[key] = value
        required = [k for k in string_params[command.intent] if k not in {"path"} or command.intent not in {"file_list", "file_find"}]
        if any(not cleaned.get(key) for key in required):
            return _command("unknown", command.original_text)
        return Command(command.intent, cleaned, command.original_text)

    if command.intent in {"remember", "forget", "recall_memory"}:
        key = str(command.parameters.get("key", "")).strip()
        if not key:
            return _command("unknown", command.original_text)

    required_by_intent = {
        "email_send": ("to", "subject", "body"),
        "email_reply": ("message_id", "body"),
        "calendar_create": ("summary", "start", "end"),
        "task_add": ("title",),
        "task_complete": ("identifier",),
        "task_delete": ("identifier",),
        "google_task_add": ("title",),
        "google_task_complete": ("identifier",),
        "google_task_delete": ("identifier",),
        "reminder_add": ("message", "when"),
        "reminder_cancel": ("identifier",),
        "vision_image": ("path",),
        "smart_home_action": ("device", "action"),
    }
    if command.intent in required_by_intent:
        cleaned = dict(command.parameters)
        for key in required_by_intent[command.intent]:
            if not str(cleaned.get(key, "")).strip():
                return _command("unknown", command.original_text)
            cleaned[key] = str(cleaned[key]).strip()
        return Command(command.intent, cleaned, command.original_text)

    if command.intent in {
        "email_list",
        "calendar_list",
        "task_list",
        "google_task_list",
        "reminder_list",
        "vision_screen",
    }:
        if command.intent == "email_list":
            return Command("email_list", {"query": str(command.parameters.get("query", "in:inbox")).strip()}, command.original_text)
        return command

    return command


def validar_command(command: Command) -> Command:
    return _validate_command(command)


def _interpret_with_llm(texto: str) -> Command:
    schema = {"intent": "uma das intents permitidas", "parameters": "objeto com parâmetros simples"}
    prompt = f"""
Você é o interpretador do assistente {ASSISTANT_NAME}.
Sua função é classificar a intenção do usuário e devolver SOMENTE JSON válido.
Nunca execute ações. Apenas interprete.
O idioma pode ser português ou inglês.

Intents permitidas:
{", ".join(sorted(ALLOWED_INTENTS))}

Regras importantes:
- general_question para conversa normal e perguntas.
- file_list para listar conteúdo de uma pasta.
- file_find para procurar arquivos por nome.
- file_open para abrir um arquivo autorizado.
- file_create_folder para criar uma pasta.
- file_move para mover um arquivo/pasta autorizado.
- file_delete para excluir um arquivo autorizado.
- process_list para listar processos em execução.
- process_close para encerrar um processo explicitamente informado.
- open_application e close_application apenas para aplicativos nomeados.
- open_spotify_playlist para playlists.
- Nunca invente caminhos, aplicativos ou processos que o usuário não mencionou.
- Para file_list, path pode ser vazio e significa uma pasta padrão.
- Para file_find, use query e, quando informado, path.
- Para file_move, use source e destination.
- Retorne sempre um objeto JSON no formato:
{json.dumps(schema, ensure_ascii=False)}

Texto do usuário:
{texto}
""".strip()

    data = llm.gerar_json(prompt)
    intent = str(data.get("intent", "unknown")).strip()
    parameters = data.get("parameters", {})
    if not isinstance(parameters, dict):
        parameters = {}
    return _validate_command(Command(intent=intent, parameters=parameters, original_text=texto))


def interpretar(texto: str) -> Command:
    original = texto.strip()
    normalized = _normalize_text(original)
    if not normalized:
        return _command("unknown", original)

    detectors = (
        _detect_clear_memory,
        _detect_clear_context,
        _detect_remember,
        _detect_forget,
        _detect_recall_memory,
        _detect_time,
        _detect_calculator,
        _detect_spotify_playlist,
        _detect_web_search,
        _detect_web_browser,
        _detect_browser_actions,
        _detect_email_calendar_tasks,
        _detect_processes,
        _detect_close_application,
        _detect_open_application,
        _detect_system_info,
        _detect_system_control,
        _detect_file_list,
        _detect_file_find,
        _detect_file_open,
        _detect_file_create_folder,
        _detect_file_move,
        _detect_file_delete,
    )
    for detector in detectors:
        command = detector(normalized)
        if command:
            return command

    try:
        return _interpret_with_llm(original)
    except Exception as exc:
        logger.warning("Falha no interpretador LLM: %s", exc)
        return _command("general_question", original)


def responder(command: Command) -> str:
    if command.intent != "general_question":
        return ""
    return responder_pergunta(command.original_text)


def llm_name() -> str:
    return llm.last_provider
