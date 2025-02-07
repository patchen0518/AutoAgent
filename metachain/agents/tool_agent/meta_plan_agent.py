from metachain.types import Agent
from pydantic import BaseModel
from metachain.tools.meta.tool_retriever import get_api_plugin_tools_doc
from metachain.tools.meta.search_tools import search_trending_models_on_huggingface, get_hf_model_tools_doc
from metachain.tools.meta.edit_tools import list_tools
from typing import Union
from metachain.environment import DockerEnv, LocalEnv


def get_meta_plan_agent(model: str) -> Agent:
    def instructions(context_variables):
        code_env: Union[DockerEnv, LocalEnv] = context_variables.get("code_env", LocalEnv())
        instructions = f"""\
You are a helpful planner that can help `Tool Editor Agent` how to use MetaChain to solve the user's request.

Existing tools you already have: 
{list_tools(context_variables)}

You should first fully understand the user's request, then analyze the existing tools and determine which tools are needed to solve the user's request, finally, you should transfer the conversation to the `Meta Agent` with the plan of using the tools.

If existing tools are not enough for your task, you should develop new tools. 

1. [IMPORTANT] If you want to use third-party api, especially for some tasks related to Finance, Entertainment, eCommerce, Food, Travel, Sports, you MUST use the `get_api_plugin_tools_doc` tool to search information from existing api documents, it contains how to implement the api and API keys.


2. [IMPORTANT] If you want to use Hugging Face models, especially for some tasks related to vision, audio, video, you should use the `search_trending_models_on_huggingface` tool to search trending models related to the specific task on Hugging Face, and then use the `get_hf_model_tools_doc` tool to get the detailed information about the specific model.

3. [IMPORTANT] As for the tags ['image-text-to-text', 'visual-question-answering', 'video-text-to-text'] and ANY visual tasks, you should use `visual_question_answering` tool instead of Hugging Face models.

4. [IMPORTANT] You can not use `transfer_back_to_meta_agent_with_plans` util you have fully understood the user's request and have try your best to search information from exsiting resources if you want to create a new tool.
"""
        return instructions
    return Agent(
        name="Meta Plan Agent",
        model=model,
        instructions=instructions,
        functions=[get_api_plugin_tools_doc, search_trending_models_on_huggingface, get_hf_model_tools_doc],
        tool_choice = "required", 
        parallel_tool_calls = False
    )
