from app.models.agent import Agent
from app.models.agent_fab import AgentFab
from app.models.agent_version import AgentVersion
from app.schemas.agent_card import (
    AgentCard,
    AgentCardCapabilities,
    AgentCardInterface,
    AgentCardProvider,
)

# Every AgentFab a version deploys to becomes one supportedInterfaces entry — a
# single protocol binding for now (this app has no notion of a version being
# reachable over more than one protocol). See docs/superpowers/specs for the
# field-by-field mapping this was built against.
_PROTOCOL_BINDING = "JSONRPC"
_PROTOCOL_VERSION = "1.0"


def build_agent_card(agent: Agent, agent_version: AgentVersion, fabs: list[AgentFab]) -> AgentCard:
    return AgentCard(
        name=agent.name,
        description=agent.description,
        supportedInterfaces=[
            AgentCardInterface(
                url=fab.url, protocolBinding=_PROTOCOL_BINDING, protocolVersion=_PROTOCOL_VERSION
            )
            for fab in fabs
            if fab.url
        ],
        provider=AgentCardProvider(organization=agent.provider, url=None)
        if agent.provider
        else None,
        iconUrl=agent.icon_path,
        version=str(agent_version.version),
        capabilities=AgentCardCapabilities(streaming=agent_version.streaming),
        defaultInputModes=agent_version.default_input_modes,
        defaultOutputModes=agent_version.default_output_modes,
        skills=agent_version.skills,
    )
