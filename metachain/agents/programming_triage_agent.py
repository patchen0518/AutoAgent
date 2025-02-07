from metachain.types import Agent
from metachain.tools import (
    gen_code_tree_structure, execute_command, read_file, create_file, write_file, list_files, create_directory, run_python, code_rag, case_resolved, get_api_plugin_tools_doc
)
from metachain.util import make_message, make_tool_message
from metachain.registry import register_agent

@register_agent(name = "Tool Creation Agent", func_name="get_tool_creation_agent")
def get_tool_creation_agent(model: str):
    def tool_creation_instructions(context_variables):
        working_dir = context_variables.get("working_dir", None)
        return \
    f"""You are working on an agent project named 'metachain' whose path is /{working_dir}/metachain.
    Your task is to develop new tools in the `/{working_dir}/metachain/metachain/tools` folder.

    Follow the following instructions to develop new tools:

    1. If you want to create new tools, you should first create a new file in the `metachain/metachain/tools` directory, write the function, and then add the function to the `metachain/metachain/tools/__init__.py`. Note that when add new tools into `__init__.py`, you first read the file content and keep the original content, then add the new tools into the file.
    2. The tool is python functions. 
    3. When developing a new tool, you should follow the coding style of the existing tools, which means you should write docstring for the function, and add some useful comments to explain the code.
    4. Function should usually return a `str` (values will be attempted to be cast as a `str`).
    5. If there is any error during the development process, you should use tools to debug the error and fix the error, and you should not transfer the conversation back to the 'Programming Triage Agent' util the error is fixed. 
    6. If you need to develop a new tool through external API, you should use `get_api_plugin_tools_doc` tool to get the tool doc, such as websearch, news search, financial tools, etc, otherwise you should develop a new tool by yourself.
    7. If you need to develop a new tool related to vector database, you should use the pre-built class `Memory` in `/{working_dir}/metachain/metachain/memory/rag_memory.py` to save and retrieve the data.
    8. You can add `if __name__ == "__main__":` at the end of the function file to make sure the function can be executed, and after testing all functions you should develop, using `transfer_back_to_programming_triage_agent` function to transfer the conversation back to the 'Programming Triage Agent', note that you should not transfer the conversation back to the 'Programming Triage Agent' util you finish the your task that is to develop all the tools and make sure they can be executed.

    Note that if you need OPENAI_API_KEY, my key is: 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
    """
    return Agent(
    name="Tool Creation Agent",
    model=model,
    instructions=tool_creation_instructions,
    functions=[gen_code_tree_structure, execute_command, read_file, create_file, write_file, list_files, create_directory, run_python, code_rag, get_api_plugin_tools_doc],
    tool_choice = "auto", 
    parallel_tool_calls = False
    )

@register_agent(name = "Agent Creation Agent", func_name="get_agent_creation_agent")
def get_agent_creation_agent(model: str):
    def agent_creation_instructions(context_variables):
        working_dir = context_variables.get("working_dir", None)
        return \
    f"""You are working on an agent project named 'metachain' whose path is /{working_dir}/metachain.
    Your task is to develop new agents in the `/{working_dir}/metachain/metachain/agents` folder.

    Follow the following instructions to develop new agents:

    1. If you want to create new agents, you should first create a new file in the `metachain/metachain/agents` directory, write the function `get_xxx_agent(model: str)`, and then add the function to the `metachain/metachain/agents/__init__.py`. Note that when add new agents into `__init__.py`, you first read the file content and keep the original content, then add the new agents into the file.
    2. In this stage, you should not run the agent, you should only develop the agent.
    3. You may need to develop more than one agent, and in this stage you should not concern the relationship between agents.
    4. After developing a new agent, you should use `transfer_back_to_programming_triage_agent` function to transfer the conversation back to the 'Programming Triage Agent', note that you should not transfer the conversation back to the 'Programming Triage Agent' util you finish the your task that is to develop all the agents.


    And there is a guide for you to follow:

    """+\
    r"""An `Agent` simply encapsulates a set of `instructions` with a set of `functions` (plus some additional settings below), and has the capability to hand off execution to another `Agent`.

    While it's tempting to personify an `Agent` as "someone who does X", it can also be used to represent a very specific workflow or step defined by a set of `instructions` and `functions` (e.g. a set of steps, a complex retrieval, single step of data transformation, etc). This allows `Agent`s to be composed into a network of "agents", "workflows", and "tasks", all represented by the same primitive.

    ### `Agent` Fields

    | Field            | Type                     | Description                                                  | Default                      |
    | ---------------- | ------------------------ | ------------------------------------------------------------ | ---------------------------- |
    | **name**         | `str`                    | The name of the agent.                                       | `"Agent"`                    |
    | **model**        | `str`                    | The model to be used by the agent.                           | `"gpt-4o"`                   |
    | **instructions** | `str` or `func() -> str` | Instructions for the agent, can be a string or a callable returning a string. | `"You are a helpful agent."` |
    | **functions**    | `List`                   | A list of functions that the agent can call.                 | `[]`                         |
    | **tool_choice**  | `str`                    | The tool choice for the agent, if any.                       | `None`                       |

    #### Instructions

    `Agent` `instructions` are directly converted into the `system` prompt of a conversation (as the first message). Only the `instructions` of the active `Agent` will be present at any given time (e.g. if there is an `Agent` handoff, the `system` prompt will change, but the chat history will not.)

    ```python
    agent = Agent(
    instructions="You are a helpful agent."
    )
    ```

    The `instructions` can either be a regular `str`, or a function that returns a `str`. The function can optionally receive a `context_variables` parameter, which will be populated by the `context_variables` passed into `client.run()`.

    ```python
    def instructions(context_variables):
    user_name = context_variables["user_name"]
    return f"Help the user, {user_name}, do whatever they want."

    agent = Agent(
    instructions=instructions
    )
    response = client.run(
    agent=agent,
    messages=[{"role":"user", "content": "Hi!"}],
    context_variables={"user_name":"John"}
    )
    print(response.messages[-1]["content"])
    ```

    ```
    Hi John, how can I assist you today?
    ```
    """
    return Agent(
    name="Agent Creation Agent",
    model=model,
    instructions=agent_creation_instructions,
    functions=[gen_code_tree_structure, execute_command, read_file, create_file, write_file, list_files, create_directory, run_python, code_rag],
    tool_choice = "auto", 
    parallel_tool_calls = False
    )

@register_agent(name = "Workflow Run Agent", func_name="get_workflow_run_agent")
def get_workflow_run_agent(model: str):
    def workflow_run_instructions(context_variables):
        working_dir = context_variables.get("working_dir", None)
        return \
    f"""You are working on an agent project named 'metachain' whose path is /{working_dir}/metachain.
    Your task is to run workflows to complete the user request.

    Follow the following instructions to run workflows:

    1. The workflow is a directed graph represented by a dictionary, with the format: 
    """ +\
    r"""
    {
        "type": "object",
        "properties": {
            "nodes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "agent_name": {"type": "string"},
                        "agent_tools": {"type": "array", "items": {"type": "string"}}, 
                        "input": {"type": "string"},
                        "output": {"type": "string"},
                        "is_start": {"type": "boolean"},
                        "is_end": {"type": "boolean"}
                    },
                    "required": ["agent_name", "agent_tools", "input", "output", "is_start", "is_end"],
                    "additionalProperties": False
                }
            },
            "edges": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "start": {"type": "string"},
                        "end": {"type": "string"},
                        "description": {"type": "string"}
                    },
                    "required": ["start", "end", "description"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["nodes", "edges"],
        "additionalProperties": False
    }
    2. First create a python script named `run_xxx_workflow.py` in the `/{working_dir}/metachain` directory, and the workflow graph should be instantiated by `Graph` class in `metachain/metachain/workflow/flowgraph.py`, using `Graph.from_dict()` method.
    3. After instantiating the workflow graph, you should use `FlowEngine` class in `metachain/metachain/workflow/flowengine.py`, using `FlowEngine(g = g, model=model)` to instantiate the workflow engine.
    4. Then you can use `engine.run_meta(query, context_variables = context_variables, debug = True)` to run the workflow。
    5. After running the workflow, you should tell the 'Programming Triage Agent' final running results and use `transfer_back_to_programming_triage_agent` function to transfer the conversation back to the 'Programming Triage Agent'.
    6. If there is any error during the running process, you should use tools to debug the error and fix the error, and you should not transfer the conversation back to the 'Programming Triage Agent' util the error is fixed.

    """+\
    r"""
    There is an example to run a workflow based on the 'metachain' project: 

    ```python
    from metachain.workflow import Graph, FlowEngine
    from metachain.types import Response
    import os
    os.environ["OPENAI_API_KEY"] = "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"
    model = 'gpt-4o-2024-08-06'
    workflow_dict = {
        "nodes": [
            {
                "agent_name": "user_request",
                "agent_tools": [],
                "input": "PDF file",
                "output": "PDF file",
                "is_start": True,
                "is_end": False
            },
            {
                "agent_name": "read_pdf_agent",
                "agent_tools": [
                    "read_pdf"
                ],
                "input": "PDF file",
                "output": "Extracted text",
                "is_start": False,
                "is_end": False
            },
            {
                "agent_name": "chunk_text_agent",
                "agent_tools": [
                    "chunk_text"
                ],
                "input": "Extracted text",
                "output": "Chunked text",
                "is_start": False,
                "is_end": False
            },
            {
                "agent_name": "vectordb_agent",
                "agent_tools": [
                    "vectordb_save"
                ],
                "input": "Chunked text",
                "output": "Text saved to VectorDB",
                "is_start": False,  
                "is_end": False
            },
            {
                "agent_name": "retrieve_vectordb_agent",
                "agent_tools": [
                    "retrieve_vectordb"
                ],
                "input": "Text saved to VectorDB",
                "output": "Method section text",
                "is_start": False,
                "is_end": False
            },
            {
                "agent_name": "output",
                "agent_tools": [],
                "input": "Method section text",
                "output": "Description of Method section",
                "is_start": False,
                "is_end": True
            }
        ],
        "edges": [
            {
                "start": "user_request",
                "end": "read_pdf_agent",
                "description": "Send PDF to be read."
            },
            {
                "start": "read_pdf_agent",
                "end": "chunk_text_agent",
                "description": "Send extracted text for chunking."
            },
            {
                "start": "chunk_text_agent",
                "end": "vectordb_agent",
                "description": "Save chunked text to VectorDB."
            },
            {
                "start": "vectordb_agent",
                "end": "retrieve_vectordb_agent",
                "description": "Retrieve Method section."
            },
            {
                "start": "retrieve_vectordb_agent",
                "end": "output",
                "description": "Output of Method section text."
            }
        ]
    }
    g = Graph.from_dict(workflow_dict)
    engine = FlowEngine(g = g, model=model)

    query = 'I have a paper in the pdf format, and I want to know what the method section is about.'
    context_variables = {}
    response: Response = engine.run_meta(query, context_variables = context_variables, debug = True)
    print(response.messages[-1]['content'])
    ```
    """
    return Agent(
    name="Workflow Run Agent",
    model=model,
    instructions=workflow_run_instructions,
    functions=[gen_code_tree_structure, execute_command, read_file, create_file, write_file, list_files, create_directory, run_python, code_rag],
    tool_choice = "auto", 
    parallel_tool_calls = False
    )
@register_agent(name = "Agent Run Agent", func_name="get_agent_run_agent")
def get_agent_run_agent(model: str):
    def agent_run_instructions(context_variables):
        working_dir = context_variables.get("working_dir", None)
        return \
    f"""You are working on an agent project named 'metachain' whose path is /{working_dir}/metachain.
    Your task is to run agents to complete the user request.

    Follow the following instructions to run agents:

    1. To complete the user request using 'metachain' project, you need to run the agent by creating a python file named `run_xxx_agent.py` in the 'metachain' directory, and use `run_python` function to run the agent.
    2. If there is any error during the running process, you should use tools to debug the error and fix the error, and you should not transfer the conversation back to the 'Programming Triage Agent' util the error is fixed.
    3. After running the agent, you should tell the 'Programming Triage Agent' final running results and use `transfer_back_to_programming_triage_agent` function to transfer the conversation back to the 'Programming Triage Agent', note that you should not transfer the conversation back to the 'Programming Triage Agent' util you finish the your task that is to run all the agents.

    Note that if you need OPENAI_API_KEY, my key is: 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

    And there is a guide for you to follow:

    """+\
    r"""
    ```python
    from metachain import MetaChain
    from metachain.agents import get_programming_agent

    client = MetaChain()
    programming_agent = get_programming_agent(model)
    context_variables = {"key": value}
    messages = [{"role": "user", "content": task_instructions}]
    response = client.run(agent=programming_agent, messages=messages, context_variables=context_variables, debug=True)
    ```

    ### `client.run()`

    MetaChain's `run()` function is analogous to the `chat.completions.create()` function in the Chat Completions API - it takes `messages` and returns `messages` and saves no state between calls. Importantly, however, it also handles Agent function execution, hand-offs, context variable references, and can take multiple turns before returning to the user.

    At its core, MetaChain's `client.run()` implements the following loop:

    1. Get a completion from the current Agent
    2. Execute tool calls and append results
    3. Switch Agent if necessary
    4. Update context variables, if necessary
    5. If no new function calls, return

    #### Arguments

    | Argument              | Type    | Description                                                  | Default        |
    | --------------------- | ------- | ------------------------------------------------------------ | -------------- |
    | **agent**             | `Agent` | The (initial) agent to be called.                            | (required)     |
    | **messages**          | `List`  | A list of message objects, identical to [Chat Completions `messages`](https://platform.openai.com/docs/api-reference/chat/create#chat-create-messages) | (required)     |
    | **context_variables** | `dict`  | A dictionary of additional context variables, available to functions and Agent instructions | `{}`           |
    | **max_turns**         | `int`   | The maximum number of conversational turns allowed           | `float("inf")` |
    | **model_override**    | `str`   | An optional string to override the model being used by an Agent | `None`         |
    | **execute_tools**     | `bool`  | If `False`, interrupt execution and immediately returns `tool_calls` message when an Agent tries to call a function | `True`         |
    | **stream**            | `bool`  | If `True`, enables streaming responses                       | `False`        |
    | **debug**             | `bool`  | If `True`, enables debug logging                             | `False`        |

    Once `client.run()` is finished (after potentially multiple calls to agents and tools) it will return a `Response` containing all the relevant updated state. Specifically, the new `messages`, the last `Agent` to be called, and the most up-to-date `context_variables`. You can pass these values (plus new user messages) in to your next execution of `client.run()` to continue the interaction where it left off – much like `chat.completions.create()`. (The `run_demo_loop` function implements an example of a full execution loop in `/MetaChain/repl/repl.py`.)

    #### `Response` Fields

    | Field                 | Type    | Description                                                  |
    | --------------------- | ------- | ------------------------------------------------------------ |
    | **messages**          | `List`  | A list of message objects generated during the conversation. Very similar to [Chat Completions `messages`](https://platform.openai.com/docs/api-reference/chat/create#chat-create-messages), but with a `sender` field indicating which `Agent` the message originated from. |
    | **agent**             | `Agent` | The last agent to handle a message.                          |
    | **context_variables** | `dict`  | The same as the input variables, plus any changes.           |
    """
    return Agent(
    name="Agent Run Agent",
    model=model,
    instructions=agent_run_instructions,
    functions=[gen_code_tree_structure, execute_command, read_file, create_file, write_file, list_files, create_directory, run_python, code_rag],
    tool_choice = "auto", 
    parallel_tool_calls = False
    )
@register_agent(name = "Programming Triage Agent", func_name="get_programming_triage_agent")
def get_programming_triage_agent(model: str):
    def programming_triage_instructions(context_variables):
        working_dir = context_variables.get("working_dir", None)
        ret_instructions =  \
    f"""You are a programmer working on an agent project named 'metachain' whose path is /{working_dir}/metachain.

    Your overall task is using existing project to create agents or workflows to complete the user request. 

    If the existing tools or agents are not enough for your task, you should develop new tools or agents. 
    And you should determine which agent is best suited to handle the user's request, and transfer the conversation to that agent based on the following routine: 

    1. If you need to develop new tools, transfer the conversation to the 'Tool Creation Agent' to create a new tool in the `/{working_dir}/metachain/metachain/tools` folder using function `transfer_to_tool_creation_agent`.
    2. If you need to develop new agents, transfer the conversation to the 'Agent Creation Agent' to create a new agent in the `/{working_dir}/metachain/metachain/agents` folder using function `transfer_to_agent_creation_agent`.
    3. After there is enough pre-built tools and agents, transfer the conversation to the 'Agent Run Agent' or 'Workflow Run Agent' to create agents or workflows to complete the user request using function `transfer_to_agent_run_agent` or `transfer_to_workflow_run_agent`.
    4. Note that if you should create both new tools and new agents, you should create the new tools first, and then create the new agents. 

    Note that if there are not enough pre-built tools, you should develop new tools first, and then develop new agents, and finally run the workflow or agent to complete the user request.

    Once you receive the develop plan, you should not stop util you finish the task. 
    """
        how_to_guides = context_variables.get("how_to_guides", None)
        if how_to_guides:
            ret_instructions += \
    f"""
    If you want to develop new tools or agents, you should follow the following guides:
    {how_to_guides}
    """
        return ret_instructions
    tool_creation_agent = get_tool_creation_agent(model)
    agent_creation_agent = get_agent_creation_agent(model)
    workflow_run_agent = get_workflow_run_agent(model)
    agent_run_agent = get_agent_run_agent(model)
    def transfer_to_tool_creation_agent(input: str):
        return tool_creation_agent
    def transfer_to_agent_creation_agent(input: str):
        return agent_creation_agent
    def transfer_to_workflow_run_agent(input: str):
        return workflow_run_agent
    def transfer_to_agent_run_agent(input: str):
        return agent_run_agent
    programming_triage_agent =  Agent(
    name="Programming Triage Agent",
    model=model,
    instructions=programming_triage_instructions,
    functions=[transfer_to_tool_creation_agent, transfer_to_agent_creation_agent, transfer_to_workflow_run_agent, transfer_to_agent_run_agent],
    tool_choice = "auto", 
    parallel_tool_calls = False
    )
    def transfer_back_to_programming_triage_agent():
        """Call this function if the existing agent has already finished the sub-task."""
        return programming_triage_agent
    tool_creation_agent.functions.append(transfer_back_to_programming_triage_agent)
    agent_creation_agent.functions.append(transfer_back_to_programming_triage_agent)
    workflow_run_agent.functions.append(transfer_back_to_programming_triage_agent)
    agent_run_agent.functions.append(transfer_back_to_programming_triage_agent)
    return programming_triage_agent


if __name__ == "__main__":
    print(agent_creation_instructions({"working_dir": "metachain"}))
