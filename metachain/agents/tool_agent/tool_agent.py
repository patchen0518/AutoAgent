from metachain.registry import register_agent
from metachain.types import Agent, Result
from metachain.environment import DockerEnv, LocalEnv
from metachain.tools.meta.edit_tools import list_tools
from metachain.agents.tool_agent.tool_editor import get_tool_editor_agent
from typing import Union
from metachain.tools.inner import case_resolved, case_not_resolved
from pydantic import BaseModel
from metachain.util import function_to_json
from metachain.agents.tool_agent.meta_plan_agent import get_meta_plan_agent

class ToolDescription(BaseModel): 
    tool_functionalities: str
    existing: bool
    tool_docs: str

class ToolPlan(BaseModel): 
    tool_name: str
    tool_description: ToolDescription

@register_agent(name = "Tool Agent", func_name="get_tool_agent")
def get_tool_agent(model: str) -> Agent:
    """
    The tool agent is an agent that can be used to create and run other tools.
    """
    def instructions(context_variables):
        code_env: Union[DockerEnv, LocalEnv] = context_variables.get("code_env", LocalEnv())
        instructions = f"""\
You are a helpful assistant that can help the user with their request by creating and running tools in the Metachain agent framework. Your responsibility is to determine which sub-agent is best suited to handle the user's request under the current context, and transfer the conversation to that sub-agent. And you should not stop to try to solve the user's request by transferring to another sub-agent only until the task is completed.

Your sub-agents are: 
1. `Meta Plan Agent`: This agent is used to plan how to use MetaChain to solve the user's request.
2. `Tool Editor Agent`: This agent is used to run and edit tools.

Existing tools you already have: 
{list_tools(context_variables)}

You should first transfer the conversation to the `Meta Plan Agent` to plan how to use MetaChain to solve the user's request, and the plan should follow the following constraints: 

1. If exising tools are enough for your task, you can directly use them to solve the user's request.

2. If exising tools are not enough for your task, `Meta Plan Agent` should search information from the resources and plan how to create new tools.

3. [IMPORTANT] As for the tags ['image-text-to-text', 'visual-question-answering', 'video-text-to-text'] and ANY visual tasks, you should use `visual_question_answering` tool instead of Hugging Face models.
"""
        return instructions
    
    tool_editor_agent: Agent = get_tool_editor_agent(model)
    meta_plan_agent: Agent = get_meta_plan_agent(model)
    def transfer_to_tool_editor_agent(sub_task: str):
        """
        Args: 
            sub_task: The detailed description of the sub-task that the `Meta Agent` will ask the `Tool Editor Agent` to do.
        """
        return tool_editor_agent
    def transfer_to_meta_plan_agent(sub_task: str):
        """
        Use this function when you want to plan how to use MetaChain to solve the user's request.
        Args: 
            sub_task: The detailed description of the sub-task that the `Meta Agent` will ask the `Meta Plan Agent` to do.
        """
        return meta_plan_agent
    meta_agent = Agent(
        name="Meta Agent", 
        model=model, 
        instructions=instructions,
        functions=[transfer_to_meta_plan_agent, transfer_to_tool_editor_agent, case_resolved, case_not_resolved], 
        tool_choice = "required", 
        parallel_tool_calls = False
    )
    
    def transfer_back_to_meta_agent(task_status: str):
        """
        Args: 
            task_status: The status of the task that the `Meta Agent` will ask the `Meta Agent` to do.
        """
        return meta_agent
    def transfer_back_to_meta_agent_with_plans(tool_development_steps: list[ToolPlan]) -> str:
        """
        This function is used to plan how to use MetaChain to solve the user's request. You can use this function only after you have fully understood the user's request and have try your best to search information from exsiting resources.

        Args: 
            tool_development_steps: The steps of tool development. It is a list of dictionaries, each dictionary contains the tools name you should use in the exsiting MetaChain or the tools name you should develop. If the tool is not existing, dictionaries should contain the tool documentation.
        """
        tool_str = "\n".join([f"{tool['tool_name']}: {tool['tool_description']['tool_functionalities']} [{tool['tool_description']['existing']}]" for tool in tool_development_steps])
        ret_val = f"""\
    Receiving user's request, I have the following plans to use MetaChain to solve the user's request: 
    As for using existing tools, I have the following plans: 
    {tool_str}
    """
        return Result(
            value=ret_val, 
            agent=meta_agent
        )
    
    tool_editor_agent.functions.append(transfer_back_to_meta_agent)
    meta_plan_agent.functions.append(transfer_back_to_meta_agent_with_plans)
    
    return meta_agent

