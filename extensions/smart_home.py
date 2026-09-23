from __future__ import annotations

from abc import ABC, abstractmethod

import httpx

from core.config import ESP32_BASE_URL, HOME_ASSISTANT_TOKEN, HOME_ASSISTANT_URL, SMART_HOME_PROVIDER


class SmartHomeProvider(ABC):
    @abstractmethod
    def execute(self, device: str, action: str, parameters: dict | None = None) -> str:
        raise NotImplementedError


class DisabledSmartHomeProvider(SmartHomeProvider):
    def execute(self, device: str, action: str, parameters: dict | None = None) -> str:
        return "A integração de Smart Home ainda está desativada."


class HomeAssistantProvider(SmartHomeProvider):
    def execute(self, device: str, action: str, parameters: dict | None = None) -> str:
        if not HOME_ASSISTANT_URL or not HOME_ASSISTANT_TOKEN:
            return "Home Assistant não está configurado."
        parameters = parameters or {}
        domain = parameters.get("domain", "homeassistant")
        service = parameters.get("service", action)
        entity_id = parameters.get("entity_id", device)
        payload = {k: v for k, v in parameters.items() if k not in {"domain", "service", "entity_id"}}
        payload["entity_id"] = entity_id
        response = httpx.post(
            f"{HOME_ASSISTANT_URL}/api/services/{domain}/{service}",
            headers={"Authorization": f"Bearer {HOME_ASSISTANT_TOKEN}"},
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        return f"Ação enviada ao Home Assistant: {domain}.{service}."


class ESP32Provider(SmartHomeProvider):
    def execute(self, device: str, action: str, parameters: dict | None = None) -> str:
        if not ESP32_BASE_URL:
            return "ESP32 não está configurado."
        response = httpx.post(
            f"{ESP32_BASE_URL}/api/action",
            json={"device": device, "action": action, "parameters": parameters or {}},
            timeout=5,
        )
        response.raise_for_status()
        return "Ação enviada ao ESP32."


if SMART_HOME_PROVIDER == "homeassistant":
    smart_home = HomeAssistantProvider()
elif SMART_HOME_PROVIDER == "esp32":
    smart_home = ESP32Provider()
else:
    smart_home = DisabledSmartHomeProvider()
