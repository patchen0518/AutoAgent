

from metachain.types import Agent
from metachain.tools import (
    get_api_plugin_tools_doc, check_agent, check_tool
)
from metachain.registry import register_agent

@register_agent(name = "Plan Agent", func_name="get_plan_agent")
def get_plan_agent(model: str):
    def instructions(context_variables):
        working_dir = context_variables.get("working_dir", None)
        return \
f"""You are a planner working on an agent project named 'metachain' which can generate a coding plan for a given user request. 
I want to use existing project code to solve the task. You should use the tools `check_agent` and `check_tool` to carefully go through the existing code to find out whether you should develop a new agent or new tool. 
After you have checked the existing code, you should give a detailed plan for developing agents to solve the task based on the existing code, and ask user to confirm or modify the plan.
Finally, after user confirms the plan, you should generate the final coding plan and output it, and transfer the conversation to the 'Programming Triage Agent' to use the plan to execute the task util you finish the task, otherwise I will lose a lot of money.

Follow the following rules to develop new tools:

1. If you want to create new tools, you should first create a new file in the `metachain/metachain/tools` directory, write the function, and then add the function to the `metachain/metachain/tools/__init__.py`. Note that when add new tools into `__init__.py`, you first read the file content and keep the original content, then add the new tools into the file.
2. The tool is python functions. 
3. When developing a new tool, you should follow the coding style of the existing tools, which means you should write docstring for the function, and add some useful comments to explain the code.
4. Function should usually return a `str` (values will be attempted to be cast as a `str`). 
5. If you need to develop a new tool through external API, you should use `get_api_plugin_tools_doc` tool to get the tool doc, such as websearch, news search, financial tools, etc, otherwise you should develop a new tool by yourself.
6. If you need to develop a new tool related to vector database, you should use the pre-built class `Memory` in `/{working_dir}/metachain/metachain/memory/rag_memory.py` to save and retrieve the data.

Follow the following instructions to develop new agents:

1. If you want to create new agents, you should first create a new file in the `metachain/metachain/agents` directory, write the function `get_xxx_agent(model: str)`, and then add the function to the `metachain/metachain/agents/__init__.py`. Note that when add new agents into `__init__.py`, you first read the file content and keep the original content, then add the new agents into the file.

Note that your plan should fit the given rules.
"""
    return Agent(
    name="Plan Agent",
    model=model,
    instructions=instructions,
    functions=[check_agent, check_tool],
    parallel_tool_calls = False
    )