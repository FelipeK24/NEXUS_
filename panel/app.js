const API_BASE = window.NEXUS_API_URL || "";
const API_TOKEN = window.NEXUS_API_TOKEN || "";


const state = {
    connected: false,
    mode: "offline",
    locked: false,
    interactions: []
};


const orbArea =
    document.querySelector(".orb-area");


const stateLabel =
    document.getElementById("stateLabel");


const stateDescription =
    document.getElementById("stateDescription");


const connectionStatus =
    document.getElementById("connectionStatus");


const connectionDot =
    document.querySelector(".connection-dot");


const interactions =
    document.getElementById("interactions");


/* HEADERS */

function getHeaders() {

    const headers = {
        "Content-Type": "application/json"
    };


    if (API_TOKEN) {

        headers["X-NEXUS-TOKEN"] =
            API_TOKEN;

    }


    return headers;
}


/* MODO DA ORB */

function setMode(mode, description = "") {

    orbArea.classList.remove(
        "state-offline",
        "state-online",
        "state-thinking",
        "state-speaking"
    );


    orbArea.classList.add(
        `state-${mode}`
    );


    state.mode = mode;


    const labels = {

        offline: "OFFLINE",

        online: "ONLINE",

        thinking: "PENSANDO",

        speaking: "FALANDO"

    };


    stateLabel.textContent =
        labels[mode] || "NEXUS";


    stateDescription.textContent =
        description;


    const colors = {

        offline: "#777D86",

        online: "#007CC4",

        thinking: "#B98A32",

        speaking: "#8D45D8"

    };


    const color =
        colors[mode] || colors.offline;


    connectionDot.style.background =
        color;


    connectionDot.style.boxShadow =
        `0 0 10px ${color}`;

}


/* CONEXÃO */

function setConnected(connected) {

    state.connected =
        connected;


    if (!connected) {

        connectionStatus.textContent =
            "CORE OFFLINE";


        setMode(
            "offline",
            "Aguardando conexão"
        );

        return;

    }


    connectionStatus.textContent =
        "CORE CONNECTED";


    if (state.mode === "offline") {

        setMode(
            "online",
            "Sistema pronto"
        );

    }

}


/* HARDWARE */

function setMetric(
    value,
    valueId,
    barId
) {

    const number =
        Number(value);


    if (!Number.isFinite(number)) {
        return;
    }


    const safe =
        Math.max(
            0,
            Math.min(100, number)
        );


    document.getElementById(
        valueId
    ).textContent =
        `${Math.round(safe)}%`;


    document.getElementById(
        barId
    ).style.width =
        `${safe}%`;

}


function updateHardware(data) {

    if (!data) {
        return;
    }


    setMetric(
        data.cpu ??
        data.cpu_percent,

        "cpuValue",

        "cpuBar"
    );


    setMetric(
        data.ram ??
        data.ram_percent,

        "ramValue",

        "ramBar"
    );


    setMetric(
        data.gpu ??
        data.gpu_percent,

        "gpuValue",

        "gpuBar"
    );


    if (data.disk != null) {

        document.getElementById(
            "diskValue"
        ).textContent =
            `${Math.round(
                Number(data.disk)
            )}%`;

    }


    if (data.network_down != null) {

        document.getElementById(
            "networkDown"
        ).textContent =
            formatRate(
                data.network_down
            );

    }


    if (data.network_up != null) {

        document.getElementById(
            "networkUp"
        ).textContent =
            formatRate(
                data.network_up
            );

    }

}


/* VELOCIDADE DE REDE */

function formatRate(value) {

    const number =
        Number(value);


    if (!Number.isFinite(number)) {
        return "--";
    }


    if (
        number >=
        1024 * 1024
    ) {

        return (
            (number /
                1024 /
                1024
            ).toFixed(1)
            + " MB/s"
        );

    }


    if (
        number >= 1024
    ) {

        return (
            (number /
                1024
            ).toFixed(1)
            + " KB/s"
        );

    }


    return (
        number.toFixed(0)
        + " B/s"
    );

}


/* CORE */

function updateCore(data) {

    if (!data) {
        return;
    }


    document.getElementById(
        "version"
    ).textContent =
        data.version ??
        data.nexus_version ??
        "--";


    document.getElementById(
        "aiProvider"
    ).textContent =
        data.ai ??
        data.provider ??
        data.current_ai ??
        "--";


    document.getElementById(
        "skillsValue"
    ).textContent =
        data.skills ??
        data.skills_count ??
        "--";


    document.getElementById(
        "uptime"
    ).textContent =
        data.uptime ??
        "--";


    if (
        typeof data.locked ===
        "boolean"
    ) {

        state.locked =
            data.locked;

        updateLockButton();

    }


    if (
        [
            "online",
            "thinking",
            "speaking",
            "offline"
        ].includes(data.state)
    ) {

        setMode(
            data.state,

            data.state ===
            "online"
                ? "Sistema pronto"
                : ""
        );

    }

}


/* INTERAÇÕES */

function renderInteractions() {

    if (
        state.interactions.length === 0
    ) {

        interactions.innerHTML = `
            <div class="empty-interactions">
                Nenhuma interação registrada.
            </div>
        `;

        return;

    }


    interactions.innerHTML =
        state.interactions
            .map(item => `

                <div class="interaction">

                    <div class="interaction-time">
                        ${escapeHtml(
                            item.time ||
                            "--:--"
                        )}
                    </div>

                    <div class="interaction-command">
                        ${escapeHtml(
                            item.command ||
                            ""
                        )}
                    </div>

                    <div class="interaction-response">
                        ${escapeHtml(
                            item.response ||
                            ""
                        )}
                    </div>

                </div>

            `)
            .join("");

}


function addInteraction(
    command,
    response
) {

    state.interactions.unshift({

        time:
            new Date()
                .toLocaleTimeString(
                    "pt-BR",
                    {
                        hour: "2-digit",
                        minute: "2-digit"
                    }
                ),

        command:
            command,

        response:
            response

    });


    state.interactions =
        state.interactions.slice(
            0,
            40
        );


    renderInteractions();

}


/* SEGURANÇA CONTRA HTML */

function escapeHtml(value) {

    return String(value)

        .replaceAll(
            "&",
            "&amp;"
        )

        .replaceAll(
            "<",
            "&lt;"
        )

        .replaceAll(
            ">",
            "&gt;"
        )

        .replaceAll(
            '"',
            "&quot;"
        )

        .replaceAll(
            "'",
            "&#039;"
        );

}


/* API */

async function api(
    path,
    options = {}
) {

    const response =
        await fetch(
            `${API_BASE}${path}`,
            {

                ...options,

                headers: {

                    ...getHeaders(),

                    ...(options.headers || {})

                }

            }
        );


    if (!response.ok) {

        throw new Error(
            `HTTP ${response.status}`
        );

    }


    const text =
        await response.text();


    if (!text) {
        return {};
    }


    try {

        return JSON.parse(text);

    } catch {

        return {
            response: text
        };

    }

}


/* ATUALIZAR STATUS */

async function refreshStatus() {

    try {

        const data =
            await api(
                "/api/status"
            );


        setConnected(true);


        updateHardware(
            data.hardware ||
            data.system ||
            data
        );


        updateCore(
            data.core ||
            data
        );


        if (
            Array.isArray(
                data.interactions
            )
        ) {

            state.interactions =
                data.interactions
                    .slice(0, 40);

            renderInteractions();

        }


    } catch (error) {

        setConnected(false);

    }

}


/* ENVIAR COMANDO */

async function sendCommand(
    text
) {

    if (!text.trim()) {
        return;
    }


    try {

        setMode(
            "thinking",
            "Processando comando"
        );


        const data =
            await api(
                "/api/command",
                {

                    method: "POST",

                    body:
                        JSON.stringify({
                            text: text
                        })

                }
            );


        const response =
            data.response ||
            data.message ||
            "Comando processado.";


        addInteraction(
            text,
            response
        );


        setMode(
            "speaking",
            "NEXUS respondendo"
        );


        setTimeout(
            () => {

                if (
                    state.connected
                ) {

                    setMode(
                        "online",
                        "Sistema pronto"
                    );

                }

            },
            1500
        );


    } catch (error) {

        addInteraction(
            text,
            "Não foi possível comunicar com o NEXUS Core."
        );


        setMode(
            "offline",
            "Falha na comunicação"
        );

    }

}


/* LOCK */

async function toggleLock() {

    try {

        const endpoint =
            state.locked
                ? "/api/unlock"
                : "/api/lock";


        await api(
            endpoint,
            {
                method: "POST"
            }
        );


        state.locked =
            !state.locked;


        updateLockButton();


        showToast(
            state.locked
                ? "NEXUS bloqueado."
                : "NEXUS desbloqueado."
        );


    } catch {

        showToast(
            "Não foi possível alterar o LOCK."
        );

    }

}


/* BOTÃO LOCK */

function updateLockButton() {

    const button =
        document.getElementById(
            "lockButton"
        );


    button.classList.toggle(
        "active",
        state.locked
    );


    button.querySelector(
        "span"
    ).textContent =
        state.locked
            ? "◆"
            : "⌁";


    button.querySelector(
        "small"
    ).textContent =
        state.locked
            ? "UNLOCK"
            : "LOCK";

}


/* NOTIFICAÇÃO */

function showToast(
    message
) {

    const toast =
        document.getElementById(
            "toast"
        );


    toast.textContent =
        message;


    toast.classList.add(
        "show"
    );


    clearTimeout(
        window.toastTimer
    );


    window.toastTimer =
        setTimeout(
            () => {

                toast.classList.remove(
                    "show"
                );

            },
            2400
        );

}


/* RELÓGIO */

function updateClock() {

    document.getElementById(
        "clock"
    ).textContent =

        new Date()
            .toLocaleTimeString(
                "pt-BR"
            );

}


/* BOTÕES */


/* REFRESH */

document
    .getElementById(
        "refreshButton"
    )
    .addEventListener(
        "click",
        async () => {

            await refreshStatus();

            showToast(
                "Painel atualizado."
            );

        }
    );


/* LOCK */

document
    .getElementById(
        "lockButton"
    )
    .addEventListener(
        "click",
        toggleLock
    );


/* CONFIG */

document
    .getElementById(
        "configButton"
    )
    .addEventListener(
        "click",
        () => {

            showToast(
                "Configurações do NEXUS."
            );

        }
    );


/* MICROFONE */

document
    .getElementById(
        "micButton"
    )
    .addEventListener(
        "click",
        () => {

            const button =
                document.getElementById(
                    "micButton"
                );


            button.classList.toggle(
                "active"
            );


            showToast(
                "Controle do microfone acionado."
            );

        }
    );


/* LIMPAR INTERAÇÕES */

document
    .getElementById(
        "clearInteractions"
    )
    .addEventListener(
        "click",
        () => {

            state.interactions = [];

            renderInteractions();

        }
    );


/* INICIALIZAÇÃO */

updateLockButton();

setMode(
    "offline",
    "Aguardando conexão"
);

updateClock();

setInterval(
    updateClock,
    1000
);


refreshStatus();


setInterval(
    refreshStatus,
    3000
);