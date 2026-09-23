from datetime import datetime


def dizer_hora() -> str:
    return f"Agora são {datetime.now().strftime('%H:%M')}."
