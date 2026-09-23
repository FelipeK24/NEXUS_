NEXUS - MODO BANDEJA DO WINDOWS

Uso normal:
    start_background.bat

Isso inicia o NEXUS com pythonw.exe, sem abrir uma janela preta.

Painel:
    start_with_panel.bat

Bandeja do Windows:
    O icone do NEXUS aparece na area de notificacao.
    Clique com o botao direito para:
      - Abrir o painel
      - Alternar LOCK / UNLOCK
      - Encerrar o NEXUS

Inicializacao automatica:
    install_startup.bat

Remover inicializacao:
    uninstall_startup.bat

Modo desenvolvimento com terminal:
    start_jarvis.bat

Observacao:
    O modo tray grava logs em jarvis.log. Se pythonw.exe estiver rodando,
    nao espere uma janela do CMD para mostrar erros.

## Som da wake word

Quando o NEXUS reconhece "nexus", ele reproduz `assets/wake.wav`. Você pode substituir esse arquivo por outro `.wav` ou desativar o som com `WAKE_SOUND_ENABLED=false` no `.env`.
