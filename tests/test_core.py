import json
import threading
import time
from io import BytesIO
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from core.command import Command
from core.context import ConversationContext
from core.dispatcher import DispatchResult, Dispatcher
from core.events import EventBus
from core.errors import PlanningError, SecurityError, SkillError
from core.http_utils import RequestBodyError, command_text, read_json_object
from core.memory import MemoryManager
from core.planner import Planner
from core.security import SecurityManager
from core.pipeline import CommandPipeline
from core.skill import Skill
from core.command import PlannedCommand
from core.interpreter import _context, limpar_contexto
from core.api import NexusAPI
from core.panel import PanelServer, PanelState
from pathlib import Path
import pytest


def test_context():
    context = ConversationContext(max_turns=2)
    context.add_turn("oi", "olá")
    context.add_turn("teste", "ok")
    context.add_turn("terceiro", "fim")
    assert context.get_turns()[-1].user == "terceiro"
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


def test_planner_rejects_sequences_over_six_steps():
    planner = Planner()
    goal = " e depois ".join(f"acao {index}" for index in range(7))

    with pytest.raises(PlanningError, match="seis"):
        planner.plan(goal)


def test_planner_rejects_deterministic_sequence_with_unrecognized_step(monkeypatch):
    import core.planner as planner_module

    monkeypatch.setattr(planner_module, "interpretar", lambda text: Command("unknown", {}, text))

    with pytest.raises(PlanningError, match="interpretada"):
        Planner().plan("primeira acao e depois etapa ambigua")


def test_llm_planner_rejects_partial_plan_instead_of_executing_valid_subset(monkeypatch):
    import core.planner as planner_module

    monkeypatch.setattr(
        planner_module.llm,
        "gerar_json",
        lambda prompt: {
            "commands": [
                {"intent": "time", "parameters": {}},
                {"intent": "intent_invalida", "parameters": {}},
            ]
        },
    )

    with pytest.raises(PlanningError, match="valida"):
        Planner()._llm_plan("pedido composto que precisa de várias etapas")


def test_pipeline_fails_closed_when_planning_is_unsafe():
    class UnsafePlanner:
        def plan(self, text):
            raise PlanningError("invalid plan")

    class MustNotRunDispatcher:
        def dispatch_result(self, command, confirmation_callback=None):
            pytest.fail("nenhuma ação deve ser executada para um plano inválido")

    events = EventBus()
    result = CommandPipeline(
        MustNotRunDispatcher(), UnsafePlanner(), events=events
    ).execute("pedido ambíguo", speak=False, show_output=False)

    assert not result.success
    assert result.commands_executed == 0
    assert "plano seguro" in result.response
    assert [event["type"] for event in events.get_events()] == [
        "pipeline.started",
        "pipeline.failed",
    ]


def test_pipeline_preflights_every_skill_before_executing_a_composite_plan():
    calls = []

    class CompositePlanner:
        def plan(self, text):
            return [
                PlannedCommand(Command("preflight_side_effect", {}, text), 1, 2),
                PlannedCommand(Command("calculator", {}, text), 2, 2),
            ]

    dispatcher = Dispatcher(SecurityManager())
    dispatcher.register_skill(Skill("preflight_side_effect", lambda: calls.append("ran")))
    events = EventBus()
    result = CommandPipeline(
        dispatcher, CompositePlanner(), events=events
    ).execute("composite request", speak=False, show_output=False)

    assert not result.success
    assert result.commands_executed == 0
    assert calls == []
    assert [event["type"] for event in events.get_events()] == [
        "pipeline.started",
        "pipeline.failed",
    ]


def test_security_lock():
    security = SecurityManager()
    with pytest.raises(SecurityError):
        security.authorize(Command("close_application", {"application": "spotify"}))


def test_api_requires_token():
    with pytest.raises(ValueError, match="API_TOKEN"):
        NexusAPI(lambda text: text, SecurityManager(), host="127.0.0.1", port=0, token="")


def test_panel_rejects_remote_bind_without_token(tmp_path):
    with pytest.raises(ValueError, match="PANEL_TOKEN"):
        PanelServer(
            assistant_name="NEXUS",
            security=SecurityManager(),
            command_handler=lambda text: text,
            web_dir=Path(tmp_path),
            host="0.0.0.0",
            port=0,
        )


def test_dispatcher_does_not_retry_skill_after_type_error():
    dispatcher = Dispatcher(SecurityManager())
    calls = []

    def handler(value=None):
        calls.append(value)
        if value is not None:
            raise TypeError("erro ocorrido dentro da Skill")
        return "segunda execução indevida"

    dispatcher.register_skill(Skill("test_once", handler))
    result = dispatcher.dispatch_result(Command("test_once", {"value": "executar"}))

    assert not result.success
    assert calls == ["executar"]


def test_dispatcher_rejects_invalid_skill_parameters_before_call():
    dispatcher = Dispatcher(SecurityManager())
    calls = []

    def handler():
        calls.append(True)
        return "executado"

    dispatcher.register_skill(Skill("test_parameters", handler))
    result = dispatcher.dispatch_result(Command("test_parameters", {"unexpected": True}))

    assert not result.success
    assert calls == []


def test_dispatcher_reports_explicit_skill_error_as_failure():
    dispatcher = Dispatcher(SecurityManager())

    def handler():
        raise SkillError("falha prevista")

    dispatcher.register_skill(Skill("test_skill_error", handler))
    result = dispatcher.dispatch_result(Command("test_skill_error"))

    assert not result.success
    assert result.response == "falha prevista"


def test_dispatcher_does_not_guess_failure_from_response_wording():
    dispatcher = Dispatcher(SecurityManager())
    dispatcher.register_skill(
        Skill("test_empty_lookup", lambda: "Não tenho nenhuma memória registrada.")
    )

    result = dispatcher.dispatch_result(Command("test_empty_lookup"))

    assert result.success
    assert result.response == "Não tenho nenhuma memória registrada."


def test_http_json_requires_object_and_bounded_command():
    class Headers:
        def __init__(self, length, content_type="application/json"):
            self.length = str(length)
            self.content_type = content_type

        def get_content_type(self):
            return self.content_type

        def get(self, name, default=None):
            return self.length if name == "Content-Length" else default

    class Handler:
        def __init__(self, body, content_type="application/json"):
            self.headers = Headers(len(body), content_type)
            self.rfile = BytesIO(body)

    assert read_json_object(Handler(b'{"text":"oi"}')) == {"text": "oi"}
    with pytest.raises(RequestBodyError):
        read_json_object(Handler(b'["not", "an object"]'))
    with pytest.raises(RequestBodyError):
        command_text({"text": 123})
    with pytest.raises(RequestBodyError) as exc:
        command_text({"text": "x" * 5000})
    assert exc.value.status == 413


def test_api_unlock_route_actually_unlocks():
    security = SecurityManager()
    api = NexusAPI(lambda text: text, security, host="127.0.0.1", port=0, token="test-token")
    api.start()
    try:
        url = f"http://127.0.0.1:{api.server.server_address[1]}/api/unlock"
        request = Request(
            url,
            data=b"{}",
            headers={"Content-Type": "application/json", "X-NEXUS-TOKEN": "test-token"},
            method="POST",
        )
        with urlopen(request, timeout=3) as response:
            assert response.status == 200
        assert not security.locked

        lock_request = Request(
            url.replace("/api/unlock", "/api/lock"),
            data=b"{}",
            headers={"Content-Type": "application/json", "X-NEXUS-TOKEN": "test-token"},
            method="POST",
        )
        with urlopen(lock_request, timeout=3) as response:
            assert response.status == 200
        assert security.locked
    finally:
        api.stop()


def test_api_rejects_invalid_commands_and_hides_internal_errors():
    security = SecurityManager()

    def fail_command(text):
        raise RuntimeError("internal sensitive detail")

    api = NexusAPI(fail_command, security, host="127.0.0.1", port=0, token="test-token")
    api.start()
    base_url = f"http://127.0.0.1:{api.server.server_address[1]}/api/command"

    def post(body):
        request = Request(
            base_url,
            data=body,
            headers={"Content-Type": "application/json", "X-NEXUS-TOKEN": "test-token"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=3) as response:
                return response.status, response.read().decode("utf-8")
        except HTTPError as exc:
            return exc.code, exc.read().decode("utf-8")

    try:
        assert post(b'["not an object"]')[0] == 400
        assert post(b'{"text": 42}')[0] == 400
        too_long = json.dumps({"text": "x" * 5000}).encode("utf-8")
        assert post(too_long)[0] == 413
        status, response = post(b'{"text":"trigger internal error"}')
        assert status == 500
        assert "internal sensitive detail" not in response
    finally:
        api.stop()


def test_pipeline_records_skill_response_in_conversation_context():
    class OneCommandPlanner:
        def plan(self, text):
            return [PlannedCommand(Command("test_context_skill", {}, text), 1, 1)]

    class SuccessfulDispatcher:
        def dispatch_result(self, command, confirmation_callback=None):
            return DispatchResult(True, "resposta registrada", command.intent)

    limpar_contexto()
    try:
        pipeline = CommandPipeline(SuccessfulDispatcher(), OneCommandPlanner())
        result = pipeline.execute("comando de teste", speak=False, show_output=False)

        assert result.success
        turn = _context.get_turns()[-1]
        assert turn.user == "comando de teste"
        assert turn.assistant == "resposta registrada"
    finally:
        limpar_contexto()


def test_command_pipelines_serialize_execution_across_instances():
    first_started = threading.Event()
    release_first = threading.Event()
    second_started = threading.Event()
    plan_count = 0
    plan_count_lock = threading.Lock()

    class BlockingPlanner:
        def plan(self, text):
            nonlocal plan_count
            with plan_count_lock:
                plan_count += 1
                current = plan_count
            if current == 1:
                first_started.set()
                release_first.wait(timeout=2)
            else:
                second_started.set()
            return []

    planner = BlockingPlanner()
    first = CommandPipeline(object(), planner)
    second = CommandPipeline(object(), planner)
    first_thread = threading.Thread(target=first.execute, args=("primeiro",), kwargs={"show_output": False})
    second_thread = threading.Thread(target=second.execute, args=("segundo",), kwargs={"show_output": False})

    first_thread.start()
    assert first_started.wait(timeout=1)
    second_thread.start()
    try:
        time.sleep(0.05)
        assert not second_started.is_set()
    finally:
        release_first.set()
        first_thread.join(timeout=2)
        second_thread.join(timeout=2)

    assert second_started.is_set()
    assert not first_thread.is_alive()
    assert not second_thread.is_alive()


def test_event_bus_retains_bounded_history_and_supports_pagination():
    events = EventBus(history_size=3)
    received = []
    unsubscribe = events.subscribe(received.append)

    for number in range(5):
        events.publish("sample", {"number": number})

    page = events.get_events(after_id=2, limit=2)
    assert [event["id"] for event in page] == [3, 4]
    assert [event["data"]["number"] for event in events.get_events(after_id=2)] == [2, 3, 4]
    assert len(received) == 5
    assert events.latest_id() == 5

    unsubscribe()
    events.publish("sample", {"number": 5})
    assert len(received) == 5
    assert EventBus().stream_id != events.stream_id


@pytest.mark.parametrize("query", ["after_id=-1", "limit=0", "limit=101", "after_id=nope", "other=1", "limit=1&limit=2"])
def test_event_query_rejects_invalid_pagination(query):
    from core.events import parse_event_query

    with pytest.raises(ValueError):
        parse_event_query(query)


def test_api_events_are_authenticated_and_paginated():
    from core.events import event_bus

    security = SecurityManager()
    api = NexusAPI(lambda text: text, security, host="127.0.0.1", port=0, token="test-token")
    after_id = event_bus.latest_id()
    event_bus.publish("test.first", {"safe": True})
    event_bus.publish("test.second", {"safe": True})
    api.start()
    base_url = f"http://127.0.0.1:{api.server.server_address[1]}/api/events?after_id={after_id}&limit=1"

    def get(url, token=None):
        headers = {"X-NEXUS-TOKEN": token} if token else {}
        try:
            with urlopen(Request(url, headers=headers), timeout=3) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    try:
        assert get(base_url)[0] == 401
        status, first_page = get(base_url, "test-token")
        assert status == 200
        assert [event["type"] for event in first_page["events"]] == ["test.first"]
        assert first_page["next_id"] == first_page["events"][-1]["id"]
        next_url = base_url.replace(f"after_id={after_id}&limit=1", f"after_id={first_page['next_id']}&limit=1")
        status, second_page = get(next_url, "test-token")
        assert status == 200
        assert [event["type"] for event in second_page["events"]] == ["test.second"]
        invalid_status, _ = get(base_url.replace("limit=1", "limit=101"), "test-token")
        assert invalid_status == 400
    finally:
        api.stop()


def test_pipeline_publishes_sanitized_lifecycle_events():
    class OneCommandPlanner:
        def plan(self, text):
            return [PlannedCommand(Command("safe_intent", {}, text), 1, 1)]

    class SuccessfulDispatcher:
        def dispatch_result(self, command, confirmation_callback=None):
            return DispatchResult(True, "RESPOSTA_SECRETA", command.intent)

    events = EventBus()
    limpar_contexto()
    try:
        result = CommandPipeline(
            SuccessfulDispatcher(), OneCommandPlanner(), events=events
        ).execute("COMANDO_SECRETO", speak=False, show_output=False)
        records = events.get_events()

        assert result.success
        assert [event["type"] for event in records] == [
            "pipeline.started",
            "command.started",
            "command.completed",
            "pipeline.completed",
        ]
        assert records[1]["data"]["intent"] == "safe_intent"
        assert records[2]["data"]["success"] is True
        assert all("duration_ms" in record["data"] for record in (records[2], records[3]))
        assert "COMANDO_SECRETO" not in json.dumps(records)
        assert "RESPOSTA_SECRETA" not in json.dumps(records)
    finally:
        limpar_contexto()


def test_pipeline_emits_failure_if_planning_raises():
    class BrokenPlanner:
        def plan(self, text):
            raise RuntimeError("planner error")

    events = EventBus()
    with pytest.raises(RuntimeError, match="planner error"):
        CommandPipeline(object(), BrokenPlanner(), events=events).execute(
            "qualquer coisa", speak=False, show_output=False
        )

    assert [event["type"] for event in events.get_events()] == [
        "pipeline.started",
        "pipeline.failed",
    ]


def test_panel_metrics_handle_missing_disk_and_network_data(monkeypatch):
    import core.panel as panel_module

    security = SecurityManager()
    counters = iter([None, None])
    monkeypatch.setattr(panel_module.psutil, "net_io_counters", lambda: next(counters))
    monkeypatch.setattr(panel_module.psutil, "disk_usage", lambda path: (_ for _ in ()).throw(OSError("unavailable")))
    monkeypatch.setattr(panel_module.psutil, "cpu_percent", lambda interval=None: 12.5)
    monkeypatch.setattr(panel_module.psutil, "virtual_memory", lambda: type("Memory", (), {"percent": 42.0})())

    state = PanelState("NEXUS", security)
    snapshot = state.snapshot()

    assert snapshot["cpu"] == 12.5
    assert snapshot["ram"] == 42.0
    assert snapshot["disk"] is None
    assert snapshot["network_sent_kbps"] == 0.0
    assert snapshot["network_recv_kbps"] == 0.0


def test_panel_metrics_calculate_disk_and_network_rates(monkeypatch):
    import core.panel as panel_module

    security = SecurityManager()
    counters = iter([
        type("Counters", (), {"bytes_sent": 1024, "bytes_recv": 2048})(),
        type("Counters", (), {"bytes_sent": 2048, "bytes_recv": 4096})(),
    ])
    now = iter([10.0, 12.0])
    monkeypatch.setattr(panel_module.psutil, "net_io_counters", lambda: next(counters))
    monkeypatch.setattr(panel_module.time, "monotonic", lambda: next(now))
    monkeypatch.setattr(panel_module.psutil, "disk_usage", lambda path: type("Disk", (), {"percent": 71.0})())
    monkeypatch.setattr(panel_module.psutil, "cpu_percent", lambda interval=None: 5.0)
    monkeypatch.setattr(panel_module.psutil, "virtual_memory", lambda: type("Memory", (), {"percent": 33.0})())

    state = PanelState("NEXUS", security)
    snapshot = state.snapshot()

    assert snapshot["disk"] == 71.0
    assert snapshot["network_sent_kbps"] == 0.5
    assert snapshot["network_recv_kbps"] == 1.0
