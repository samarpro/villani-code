from villani_code.benchmark.agents.aider import AiderAgentRunner
from villani_code.benchmark.agents.base import AgentRunner
from villani_code.benchmark.agents.opencode import OpenCodeAgentRunner
from villani_code.benchmark.agents.villani import VillaniAgentRunner

AGENTS = {
    "villani": VillaniAgentRunner,
    "aider": AiderAgentRunner,
    "opencode": OpenCodeAgentRunner,
}


def build_agent_runner(agent: str) -> AgentRunner:
    try:
        return AGENTS[agent]()
    except KeyError as exc:
        raise ValueError(f"Unsupported agent: {agent}") from exc
