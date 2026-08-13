from typing import Any

from pydantic import BaseModel


class AgentCardInterface(BaseModel):
    url: str
    protocolBinding: str
    protocolVersion: str


class AgentCardProvider(BaseModel):
    organization: str | None
    url: str | None


class AgentCardCapabilities(BaseModel):
    streaming: bool
    # No corresponding feature exists yet (no push-notification delivery, no
    # extended-card mechanism) — hardcoded true per the user's explicit call, not
    # backed by a DB column. Revisit once those features are real.
    pushNotifications: bool = True
    extendedAgentCard: bool = True


class AgentCard(BaseModel):
    """A2A 1.0 agent card, assembled from Agent + AgentVersion + AgentFab — not
    stored anywhere, computed fresh on every request (see
    app/services/agent_card.py). Only the fields the user explicitly mapped are
    populated; A2A fields with no source data in this schema yet (securitySchemes,
    securityRequirements, signatures, documentationUrl) are omitted rather than
    guessed at.
    """

    name: str
    description: str | None
    supportedInterfaces: list[AgentCardInterface]
    provider: AgentCardProvider | None
    iconUrl: str | None
    version: str
    capabilities: AgentCardCapabilities
    defaultInputModes: list[str]
    defaultOutputModes: list[str]
    skills: list[Any]
