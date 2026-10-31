const $ = (selector) => document.querySelector(selector);

const statusPill = $("#status-pill");
const lockLabel = $("#lock-label");
const assistantState = $("#assistant-state");
const provider = $("#provider");
const providerCard = $("#provider-card");
const cpu = $("#cpu");
const ram = $("#ram");
const disk = $("#disk");
const network = $("#network");
const lastUser = $("#last-user");
const lastResponse = $("#last-response");
const intent = $("#intent");
const commandInput = $("#command-input");
const voiceButton = $("#voice-button");
const voiceStatus = $("#voice-status");
const lockButton = $("#lock-button");
const confirmationBox = $("#confirmation-box");
const confirmationText = $("#confirmation-text");
const authBox = $("#auth-box");
const panelTokenInput = $("#panel-token");
const authError = $("#auth-error");
const activityList = $("#activity-list");
const historyPanel = $("#history-panel");
const historyList = $("#history-list");
const skillsPanel = $("#skills-panel");
const skillsList = $("#skills-list");
const installButton = $("#install-button");
const installHint = $("#install-hint");
let eventCursor = Number(sessionStorage.getItem("nexus-event-cursor") || 0);
let pendingInstallPrompt = null;
let websocketConnected = false;
let activeSocket = null;
let activeSocketUrl = "";
let activeSocketToken = "";
const seenEventIds = new Set();

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let voiceRecognition = null;
let voiceActive = false;
let voiceHadResult = false;

function title(text) {
    return String(text || "--").toUpperCase();
}

function render(data) {
    const locked = Boolean(data.locked);
    const mode = data.mode || "--";
    const ia = data.last_provider || "none";

    statusPill.textContent = title(mode);
    lockLabel.textContent = locked ? "LOCK ATIVO" : "UNLOCK";
    lockLabel.style.color = locked ? "#ff6b7a" : "#77f3c4";
    assistantState.textContent = locked ? "NEXUS protegido" : "NEXUS desbloqueado";
    provider.textContent = `IA atual: ${title(ia)}`;
    providerCard.textContent = title(ia);
    cpu.textContent = `${Math.round(data.cpu || 0)}%`;
    ram.textContent = `${Math.round(data.ram || 0)}%`;
    disk.textContent = data.disk == null ? "--%" : `${Math.round(data.disk)}%`;
    network.textContent = `↓ ${Number(data.network_recv_kbps || 0).toFixed(1)} KB/s · ↑ ${Number(data.network_sent_kbps || 0).toFixed(1)} KB/s`;
    lastUser.textContent = data.last_user || "Nenhum comando ainda.";
    lastResponse.textContent = data.last_response || "Nenhuma resposta ainda.";
    intent.textContent = data.last_intent || "--";
    lockButton.textContent = locked ? "UNLOCK" : "LOCK";

    if (data.confirmation_pending) {
        confirmationBox.hidden = false;
        confirmationText.textContent = data.confirmation_description || "Confirme a ação solicitada.";
    } else {
        confirmationBox.hidden = true;
    }
    configureWebSocket(data);
}

function configureWebSocket(data) {
    if (!data.websocket_enabled) {
        if (activeSocket) activeSocket.close();
        activeSocket = null;
        activeSocketUrl = "";
        websocketConnected = false;
        return;
    }

    const token = sessionStorage.getItem("nexus-panel-token") || "";
    const url = data.websocket_public_url || `${location.protocol === "https:" ? "wss:" : "ws:"}//${location.hostname}:${data.websocket_port}`;
    if (activeSocket && activeSocketUrl === url && activeSocketToken === token && activeSocket.readyState < WebSocket.CLOSING) return;
    if (activeSocket) activeSocket.close();
    activeSocketUrl = url;
    activeSocketToken = token;
    websocketConnected = false;

    try {
        const socket = new WebSocket(url);
        activeSocket = socket;
        socket.onopen = () => socket.send(JSON.stringify({ type: "auth", token }));
        socket.onmessage = (message) => {
            let data;
            try { data = JSON.parse(message.data); } catch { return; }
            if (data.kind === "ready") {
                websocketConnected = true;
                if (sessionStorage.getItem("nexus-event-stream") !== data.stream_id) {
                    eventCursor = 0;
                    seenEventIds.clear();
                    activityList.replaceChildren();
                    sessionStorage.setItem("nexus-event-cursor", "0");
                }
                sessionStorage.setItem("nexus-event-stream", data.stream_id || "");
                refreshEvents(true);
            } else if (data.kind === "event" && data.event) {
                addActivity(data.event);
                eventCursor = Math.max(eventCursor, Number(data.event.id) || 0);
                sessionStorage.setItem("nexus-event-cursor", String(eventCursor));
            }
        };
        socket.onclose = () => {
            if (activeSocket === socket) {
                activeSocket = null;
                websocketConnected = false;
            }
        };
        socket.onerror = () => socket.close();
    } catch (error) {
        websocketConnected = false;
    }
}

async function request(path, options = {}) {
    const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
    const token = sessionStorage.getItem("nexus-panel-token");
    if (token) headers["X-NEXUS-TOKEN"] = token;
    const response = await fetch(path, {
        ...options,
        headers,
    });

    const data = await response.json();
    if (!response.ok) {
        const error = new Error(data.error || "Erro na requisição.");
        error.status = response.status;
        throw error;
    }
    return data;
}

async function refresh() {
    try {
        render(await request("/api/status"));
    } catch (error) {
        if (error.status === 401) {
            authBox.hidden = false;
            authError.textContent = "Informe o token configurado em PANEL_TOKEN.";
            return;
        }
        statusPill.textContent = "OFFLINE";
        assistantState.textContent = error.message;
    }
}

function describeEvent(event) {
    const data = event.data || {};
    if (event.type === "command.started") return `Iniciando ${data.intent || "comando"} (${data.index}/${data.total})`;
    if (event.type === "command.completed") {
        const result = data.success ? "concluído" : "falhou";
        return `${data.intent || "Comando"} ${result} · ${data.duration_ms ?? 0} ms`;
    }
    if (event.type === "pipeline.completed") {
        return `Pipeline ${data.success ? "concluído" : "com falhas"} · ${data.commands_executed}/${data.total_commands} ações`;
    }
    if (event.type === "pipeline.failed") return `Planner falhou na etapa ${data.stage || "desconhecida"}`;
    if (event.type === "security.lock_changed") return data.locked ? "NEXUS bloqueado" : "NEXUS desbloqueado";
    if (event.type === "assistant.state_changed") {
        const detail = [data.mode, data.intent].filter(Boolean).join(" · ");
        return `Estado atualizado${detail ? `: ${detail}` : ""}`;
    }
    return event.type;
}

function addActivity(event) {
    const eventKey = `${sessionStorage.getItem("nexus-event-stream") || ""}:${event.id}`;
    if (event.id != null && seenEventIds.has(eventKey)) return;
    if (event.id != null) {
        seenEventIds.add(eventKey);
        if (seenEventIds.size > 300) seenEventIds.delete(seenEventIds.values().next().value);
    }
    const empty = activityList.querySelector(".empty-activity");
    if (empty) empty.remove();
    const item = document.createElement("li");
    const label = document.createElement("span");
    const time = document.createElement("time");
    label.textContent = describeEvent(event);
    time.textContent = new Date(event.timestamp).toLocaleTimeString();
    item.append(label, time);
    activityList.prepend(item);
    while (activityList.children.length > 30) activityList.lastElementChild.remove();
}

async function refreshEvents(force = false) {
    if (websocketConnected && !force) return;
    try {
        let data = await request(`/api/events?after_id=${eventCursor}&limit=50`);
        const previousStream = sessionStorage.getItem("nexus-event-stream");
        if (previousStream !== data.stream_id) {
            eventCursor = 0;
            activityList.replaceChildren();
            data = await request("/api/events?after_id=0&limit=50");
        }
        sessionStorage.setItem("nexus-event-stream", data.stream_id || "");
        for (const event of data.events || []) {
            addActivity(event);
            eventCursor = Math.max(eventCursor, event.id);
        }
        eventCursor = Math.max(eventCursor, data.next_id || 0);
        sessionStorage.setItem("nexus-event-cursor", String(eventCursor));
    } catch (error) {
        if (error.status === 401) {
            authBox.hidden = false;
            authError.textContent = "Informe o token configurado em PANEL_TOKEN.";
        }
    }
}

function renderHistory(turns) {
    historyList.replaceChildren();
    if (!turns.length) {
        const empty = document.createElement("li");
        empty.className = "empty-activity";
        empty.textContent = "Nenhuma conversa recente.";
        historyList.append(empty);
        return;
    }

    for (const turn of [...turns].reverse()) {
        const item = document.createElement("li");
        const user = document.createElement("p");
        const assistant = document.createElement("p");
        const reuse = document.createElement("button");
        user.textContent = `VOCÊ: ${turn.user || ""}`;
        assistant.textContent = `NEXUS: ${turn.assistant || ""}`;
        reuse.type = "button";
        reuse.className = "history-reuse";
        reuse.textContent = "USAR DE NOVO";
        reuse.addEventListener("click", () => {
            commandInput.value = turn.user || "";
            commandInput.focus();
            commandInput.scrollIntoView({ behavior: "smooth", block: "center" });
        });
        item.append(user, assistant, reuse);
        historyList.append(item);
    }
}

async function refreshHistory() {
    try {
        const data = await request("/api/history");
        renderHistory(data.history || []);
    } catch (error) {
        historyList.textContent = error.message;
    }
}

async function refreshSkills() {
    try {
        const data = await request("/api/skills");
        skillsList.replaceChildren();
        for (const skill of data.skills || []) {
            const item = document.createElement("li");
            const name = document.createElement("code");
            const description = document.createElement("span");
            name.textContent = skill.intent || "";
            description.textContent = skill.description || "";
            item.append(name, description);
            skillsList.append(item);
        }
        if (!skillsList.children.length) skillsList.textContent = "Nenhuma Skill disponível.";
    } catch (error) {
        skillsList.textContent = error.message;
    }
}

async function connectPanel() {
    const token = panelTokenInput.value.trim();
    if (!token) return;
    sessionStorage.setItem("nexus-panel-token", token);
    try {
        render(await request("/api/status"));
        authBox.hidden = true;
        authError.textContent = "";
        panelTokenInput.value = "";
    } catch (error) {
        sessionStorage.removeItem("nexus-panel-token");
        authError.textContent = error.status === 401 ? "Token inválido." : error.message;
    }
}

async function sendCommand() {
    const text = commandInput.value.trim();
    if (!text) return;

    lastUser.textContent = text;
    try {
        const data = await request("/api/command", {
            method: "POST",
            body: JSON.stringify({ text }),
        });
        render(data.status);
        if (historyPanel.open) refreshHistory();
        commandInput.value = "";
    } catch (error) {
        lastResponse.textContent = error.message;
    }
}

historyPanel.addEventListener("toggle", () => {
    if (historyPanel.open) refreshHistory();
});
skillsPanel.addEventListener("toggle", () => {
    if (skillsPanel.open) refreshSkills();
});

$(".quick-commands").addEventListener("click", (event) => {
    const button = event.target.closest("button[data-command]");
    if (!button) return;
    commandInput.value = button.dataset.command || "";
    commandInput.focus();
});

async function resolveConfirmation(approved) {
    try {
        render(await request("/api/confirm", {
            method: "POST",
            body: JSON.stringify({ approved }),
        }));
    } catch (error) {
        lastResponse.textContent = error.message;
    }
}

async function toggleLock() {
    try {
        render(await request("/api/toggle", { method: "POST", body: "{}" }));
    } catch (error) {
        lastResponse.textContent = error.message;
    }
}

function setVoiceButton(active) {
    voiceButton.setAttribute("aria-pressed", String(active));
    voiceButton.textContent = active ? "■ PARAR" : "🎙️ FALAR";
    voiceButton.setAttribute("aria-label", active ? "Parar reconhecimento de voz" : "Falar comando");
    voiceButton.classList.toggle("listening", active);
}

if (!window.isSecureContext) {
    voiceButton.disabled = true;
    voiceStatus.textContent = "A entrada por voz precisa de HTTPS ou localhost.";
} else if (!SpeechRecognition) {
    voiceButton.disabled = true;
    voiceStatus.textContent = "Este navegador não oferece reconhecimento de voz. Digite o comando.";
} else {
    voiceRecognition = new SpeechRecognition();
    voiceRecognition.lang = "pt-BR";
    voiceRecognition.continuous = false;
    voiceRecognition.interimResults = false;
    voiceRecognition.maxAlternatives = 1;

    voiceRecognition.onstart = () => {
        voiceActive = true;
        voiceHadResult = false;
        setVoiceButton(true);
        voiceStatus.textContent = "Ouvindo… fale seu comando.";
    };

    voiceRecognition.onresult = (event) => {
        const transcript = event.results?.[event.resultIndex]?.[0]?.transcript?.trim();
        if (!transcript) return;
        const existing = commandInput.value.trim();
        commandInput.value = existing ? `${existing} ${transcript}` : transcript;
        voiceHadResult = true;
        commandInput.focus();
        voiceStatus.textContent = "Comando transcrito. Revise antes de executar.";
    };

    voiceRecognition.onerror = (event) => {
        const messages = {
            "not-allowed": "Permita o acesso ao microfone nas configurações do navegador.",
            "service-not-allowed": "O navegador bloqueou o serviço de reconhecimento de voz.",
            "audio-capture": "Não encontrei um microfone disponível.",
            "no-speech": "Não detectei fala. Toque no microfone para tentar novamente.",
            network: "O reconhecimento de voz está indisponível pela rede.",
        };
        if (event.error !== "aborted") {
            voiceStatus.textContent = messages[event.error] || "Não consegui reconhecer a fala. Tente novamente ou digite.";
        }
    };

    voiceRecognition.onend = () => {
        voiceActive = false;
        setVoiceButton(false);
        if (!voiceHadResult && voiceStatus.textContent === "Ouvindo… fale seu comando.") {
            voiceStatus.textContent = "Toque no microfone e fale seu comando.";
        }
    };

    voiceButton.addEventListener("click", () => {
        if (voiceActive) {
            voiceRecognition.stop();
            return;
        }
        try {
            voiceRecognition.start();
        } catch (error) {
            voiceStatus.textContent = "Não consegui iniciar o microfone. Aguarde um instante e tente novamente.";
        }
    });
}

installButton.addEventListener("click", async () => {
    if (!pendingInstallPrompt) return;
    pendingInstallPrompt.prompt();
    await pendingInstallPrompt.userChoice;
    pendingInstallPrompt = null;
    installButton.hidden = true;
});

window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    pendingInstallPrompt = event;
    installButton.hidden = false;
    installHint.hidden = true;
});

window.addEventListener("appinstalled", () => {
    pendingInstallPrompt = null;
    installButton.hidden = true;
    installHint.hidden = true;
});

const isStandalone = window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone;
const isAppleMobile = /iPhone|iPad|iPod/.test(window.navigator.userAgent);
if (!isStandalone && isAppleMobile) {
    installHint.textContent = "Para instalar, toque em Compartilhar e escolha Adicionar à Tela de Início.";
    installHint.hidden = false;
}

if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js").catch((error) => {
        console.warn("Não foi possível registrar o modo offline do NEXUS.", error);
    });
}

$("#send-command").addEventListener("click", sendCommand);
$("#connect-panel").addEventListener("click", connectPanel);
panelTokenInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") connectPanel();
});
$("#refresh-button").addEventListener("click", refresh);
lockButton.addEventListener("click", toggleLock);
$("#confirm-yes").addEventListener("click", () => resolveConfirmation(true));
$("#confirm-no").addEventListener("click", () => resolveConfirmation(false));
commandInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") sendCommand();
});

refresh();
refreshEvents();
setInterval(refresh, 2500);
setInterval(refreshEvents, 2000);
