from core.command import Command
from core.context import ConversationContext
from core.memory import MemoryManager
from core.planner import Planner
from core.security import SecurityManager


def test_context():
    context = ConversationContext(max_turns=2)
    context.add_turn("oi", "olá")
    context.add_turn("teste", "ok")
    context.add_turn("terceiro", "fim")
    assert context.get_last_turn().user == "terceiro"
    assert len(context.get_turns()) == 2


def test_memory(tmp_path):
    manager = MemoryManager(tmp_path / "memory.json")
    assert manager.remember("minha cor", "azul")
    assert manager.recall("minha cor") == "azul"
    assert manager.find_relevant("qual minha cor") == ("minha cor", "azul")
    assert manager.forget("minha cor")


def test_planner():
    planner = Planner()
    assert planner.split_goal("abra o spotify e depois que horas sao") == [
        "abra o spotify",
        "que horas sao",
    ]


def test_security_lock():
    security = SecurityManager()
    try:
        security.authorize(Command("close_application", {"application": "spotify"}))
    except Exception:
        return
    raise AssertionError("A ação medium deveria estar bloqueada por LOCK.")
