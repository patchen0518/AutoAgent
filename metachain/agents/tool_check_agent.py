from metachain.types import Agent
from metachain.tools import (
    get_api_plugin_tools_doc, check_tool
)
from metachain.registry import register_agent


@register_agent(name = "Tool Check Agent", func_name="get_tool_check_agent")
def get_tool_check_agent(model: str):
    def instructions(context_variables):
        return \
f"""You are a developer working on a project named 'metachain'. 
You are given a user request and required to use existing project code to solve the task.
Your goal is to enrich the functionality of existing list of tools in the `tools` folder as much as possible, so that once the similar task occurs again, the agent can solve it directly by using the tools without developing new tools.
whether you should develop some new tools to integrate into the agent to directly solve the task. 
If you use an external api, you should always develop a new tool, rather than using coding-related tools.
Answer 'Needed' or 'Not needed' first and then give your reason. ('Needed' means you should develop a new tool, 'Not needed' means you should not develop a new tool). 
You can use `check_tool` tool to review the existing tools and check whether developing a new tool is needed.
"""
    return Agent(
    name="Tool Check Agent",
    model=model,
    instructions=instructions,
    functions=[check_tool],
    parallel_tool_calls = False
    )

"""If you need to develop a new tool, you must use `get_tool_doc` tool to get the tool doc."""