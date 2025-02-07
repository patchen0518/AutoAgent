from metachain.types import Agent
from metachain.tools import (
    get_api_plugin_tools_doc, check_agent
)
from metachain.registry import register_agent

@register_agent(name = "Agent Check Agent", func_name="get_agent_check_agent")
def get_agent_check_agent(model: str):
    def instructions(context_variables):
        return \
    f"""You are a developer working on a project named 'metachain'. 
    You are given a user request and required to use existing project code to solve the task. 
    Your goal is to enrich the functionality of of existing list of agents in the `agents` folder as much as possible, so that once the similar task occurs again, the agent can solve it directly without developing new agents.
    whether you should develop a new agent to solve the task. 
    If you have already have an pre-built agent in the `agents` folder and suitable actions in the `actions` folder you could use with it, you should not develop a new agent.
    Note that the key of agent is the apprioriate `instructions` and `functions` using existing tools.
    Answer 'Needed' or 'Not needed' first and then give your reason.
    """
    return Agent(
    name="Agent Check Agent",
    model=model,
    instructions=instructions,
    functions=[check_agent],
    parallel_tool_calls = False
    )
