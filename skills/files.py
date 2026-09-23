from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from core.config import FILE_ALLOWED_ROOTS, FILE_SEARCH_LIMIT


def _expand_path(value: str) -> Path:
    text = os.path.expandvars(os.path.expanduser(str(value).strip()))
    text = text.replace("\\", os.sep)
    path = Path(text)
    if not path.is_absolute():
        alias, sep, remainder = text.partition(os.sep)
        base = FILE_ALLOWED_ROOTS.get(alias.lower()) if sep else FILE_ALLOWED_ROOTS.get(alias.lower())
        if base is not None:
            path = Path(base) / remainder if remainder else Path(base)
        else:
            path = Path.home() / text
    return path



def _find_exact_file(filename: str) -> Path | None:
    needle = Path(filename.strip().strip('"')).name.lower()
    for root_value in FILE_ALLOWED_ROOTS.values():
        root = Path(root_value).resolve(strict=False)
        if not root.is_dir():
            continue
        for candidate in root.rglob(needle):
            if candidate.is_file() and candidate.name.lower() == needle:
                return candidate.resolve()
    return None

def resolve_safe_path(value: str, *, allow_missing: bool = False) -> Path:
    if not value or not value.strip():
        raise ValueError("Caminho vazio.")

    raw = value.strip().strip('"')
    expanded = _expand_path(raw)
    candidate = expanded.resolve(strict=False)

    for root in FILE_ALLOWED_ROOTS.values():
        root_path = Path(root).resolve(strict=False)
        try:
            candidate.relative_to(root_path)
            if allow_missing or candidate.exists():
                return candidate
        except ValueError:
            continue

    raise ValueError("O caminho está fora das pastas autorizadas.")


def listar_arquivos(path: str = "downloads") -> str:
    try:
        folder = resolve_safe_path(path)
        if not folder.is_dir():
            return f"A pasta {path} não existe."
        entries = sorted(folder.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        if not entries:
            return f"A pasta {folder.name} está vazia."
        lines = []
        for item in entries[:FILE_SEARCH_LIMIT]:
            prefix = "[PASTA]" if item.is_dir() else "[ARQUIVO]"
            lines.append(f"{prefix} {item.name}")
        extra = len(entries) - len(lines)
        suffix = f" ... e mais {extra}." if extra > 0 else "."
        return f"Conteúdo de {folder}:\n" + "\n".join(lines) + suffix
    except ValueError as exc:
        return str(exc)
    except OSError as exc:
        return f"Não consegui listar a pasta: {exc}"


def encontrar_arquivo(query: str, path: str = "") -> str:
    if not query.strip():
        return "Não recebi o nome ou termo para procurar."
    try:
        roots = [resolve_safe_path(path)] if path.strip() else [Path(v).resolve() for v in FILE_ALLOWED_ROOTS.values()]
        needle = query.strip().lower()
        matches: list[Path] = []
        seen: set[Path] = set()
        for root in roots:
            if not root.is_dir():
                continue
            for item in root.rglob("*"):
                if item in seen:
                    continue
                seen.add(item)
                if item.is_file() and needle in item.name.lower():
                    matches.append(item)
                    if len(matches) >= FILE_SEARCH_LIMIT:
                        break
            if len(matches) >= FILE_SEARCH_LIMIT:
                break
        if not matches:
            return f"Não encontrei arquivos que correspondam a '{query}'."
        return "Arquivos encontrados:\n" + "\n".join(str(p) for p in matches)
    except ValueError as exc:
        return str(exc)
    except OSError as exc:
        return f"Não consegui procurar os arquivos: {exc}"


def criar_pasta(path: str) -> str:
    try:
        folder = resolve_safe_path(path, allow_missing=True)
        folder.mkdir(parents=True, exist_ok=True)
        return f"Pasta criada: {folder}"
    except ValueError as exc:
        return str(exc)
    except OSError as exc:
        return f"Não consegui criar a pasta: {exc}"


def mover_arquivo(source: str, destination: str) -> str:
    try:
        try:
            src = resolve_safe_path(source)
        except ValueError:
            src = _find_exact_file(source)
            if src is None:
                raise
        dst = resolve_safe_path(destination, allow_missing=True)
        if not src.is_file():
            return f"O arquivo de origem não existe: {src}"
        if dst.is_dir():
            dst = dst / src.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return f"Movi '{src.name}' para '{dst}'."
    except ValueError as exc:
        return str(exc)
    except OSError as exc:
        return f"Não consegui mover o arquivo: {exc}"


def excluir_arquivo(path: str) -> str:
    try:
        try:
            target = resolve_safe_path(path)
        except ValueError:
            target = _find_exact_file(path)
            if target is None:
                raise
        if not target.is_file():
            return f"O arquivo não existe: {target}"
        target.unlink()
        return f"Arquivo excluído: {target.name}."
    except ValueError as exc:
        return str(exc)
    except OSError as exc:
        return f"Não consegui excluir o arquivo: {exc}"


def abrir_arquivo(path: str) -> str:
    try:
        raw = path.strip().strip('"')
        if not Path(raw).is_absolute() and "/" not in raw and "\\" not in raw:
            target = _find_exact_file(raw)
        else:
            target = resolve_safe_path(raw)
        if target is None or not target.is_file():
            return f"O arquivo não existe: {raw}"
        if os.name != "nt":
            subprocess.Popen(["xdg-open", str(target)])
        else:
            os.startfile(str(target))
        return f"Abrindo {target.name}."
    except ValueError as exc:
        return str(exc)
    except OSError as exc:
        return f"Não consegui abrir o arquivo: {exc}"
