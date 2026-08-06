from __future__ import annotations

from typing import TYPE_CHECKING

from agents.china import ChinaNegotiator, ChinaNegotiatorConfig
from agents.usa import USANegotiator, USANegotiatorConfig

if TYPE_CHECKING:
    from services.ollama import OllamaService


class AgentFactory:
    def __init__(self, ollama_service: OllamaService):
        self._ollama = ollama_service
        self._usa_config = USANegotiatorConfig()
        self._china_config = ChinaNegotiatorConfig()

    def create_usa(self, config: USANegotiatorConfig | None = None) -> USANegotiator:
        return USANegotiator(self._ollama, config or self._usa_config)

    def create_china(self, config: ChinaNegotiatorConfig | None = None) -> ChinaNegotiator:
        return ChinaNegotiator(self._ollama, config or self._china_config)

    def create_pair(
        self,
        usa_config: USANegotiatorConfig | None = None,
        china_config: ChinaNegotiatorConfig | None = None,
    ) -> tuple[USANegotiator, ChinaNegotiator]:
        return (
            self.create_usa(usa_config),
            self.create_china(china_config),
        )

    def set_default_configs(
        self,
        usa_config: USANegotiatorConfig | None = None,
        china_config: ChinaNegotiatorConfig | None = None,
    ) -> None:
        if usa_config:
            self._usa_config = usa_config
        if china_config:
            self._china_config = china_config
