from metachain.registry import register_agent
from metachain.tools.meta.edit_tools import list_tools, create_tool, delete_tool, run_tool, get_metachain_path
from metachain.tools.meta.tool_retriever import get_api_plugin_tools_doc
from metachain.tools.meta.search_tools import search_trending_models_on_huggingface, get_hf_model_tools_doc
from metachain.types import Agent
from metachain.io_utils import read_file
from metachain.tools.terminal_tools import execute_command

def get_tool_editor_agent(model: str) -> Agent:
    """
    The tool editor is an agent that can be used to edit the tools.
    """
    def instructions(context_variables):
        return f"""\
You are a tool editor agent responsible for managing plugin tools in the MetaChain framework. Your core responsibility is to edit, create, and manage plugin tools that can be used by other agents.

[PLUGIN TOOLS SYSTEM]
- Plugin tools are the building blocks of MetaChain
- All available plugin tools are as follows:
{list_tools(context_variables)}
- Plugin tools can ONLY be executed using `run_tool(tool_name, run_code)`
- NEVER try to import and run tools directly - always use `run_tool`

[AVAILABLE MANAGEMENT TOOLS]
1. list_tools():
   - Lists all existing plugin tools
   - Returns: tool name, arguments, docstring, implementation details
   - Use this FIRST to check existing tools

2. create_tool(tool_name: str, tool_code: str):
   - Creates new plugin tools
   - Requires proper registration using @register_plugin_tool

3. run_tool(tool_name: str, run_code: str,):
   - REQUIRED method to execute any plugin tool
   - Format: run_tool("tool_name", "from metachain.tools import tool_name; print(tool_name(args))")

4. delete_tool(tool_name: str,):
   - Removes existing plugin tools
   - Use with caution

5. get_api_plugin_tools_doc:
   - Required for third-party API integrations
   - Must be used for Finance, Entertainment, etc.

6. execute_command:
   - Handles system-level operations
   - Use for dependency installation

[CRITICAL PRINCIPLES FOR PLUGIN TOOLS]
1. Tools MUST be abstract, modular, and reusable:
   - Use generic function names (e.g., `download_media` instead of `download_youtube_video`)
   - Break complex tasks into smaller, reusable components
   - Avoid task-specific implementations
   - Use parameters instead of hardcoded values

2. For ALL visual tasks (images, videos, visual analysis):
   - MUST use the existing `visual_question_answering` plugin tool
   - NO direct implementation of visual processing
   - Chain `visual_question_answering` with other tools as needed

[WORKFLOW FOR PLUGIN TOOL MANAGEMENT]
1. Always start with `list_tools()` to check existing tools
2. For new plugin tools:
   a. Design generic, reusable interface
   b. Follow the template format:
```python
{read_file('metachain/tools/dummy_tool.py')}
```
   c. Create using `create_tool`
   d. Test using `run_tool`
   e. Handle dependencies with `execute_command`

[IMPORTANT RULES]
- ALL tools must be registered with @register_plugin_tool
- ALL tools must have type hints
- Each tool does ONE thing well
- Create modular tools that can be combined
- ALWAYS use `run_tool` to execute plugin tools
- NEVER modify the `visual_question_answering` tool

[TOOL TESTING EXAMPLE]
Correct way to test a plugin tool:
```python
result = run_tool(
    tool_name="your_tool",
    run_code="from metachain.tools import your_tool; print(your_tool(param1='value1'))",
    context_variables=context_variables
)
```
"""
    tool_list = [list_tools, create_tool, run_tool, delete_tool, get_api_plugin_tools_doc, execute_command]
    return Agent(
        name="Tool Editor Agent", 
        model=model, 
        instructions=instructions,
        functions=tool_list,
        tool_choice = "required", 
        parallel_tool_calls = False
    )


"""
5. [IMPORTANT] If you want to use Hugging Face models, especially for some tasks related to vision, audio, video, you should use the `search_trending_models_on_huggingface` tool to search trending models related to the specific task on Hugging Face, and then use the `get_hf_model_tools_doc` tool to get the detailed information about the specific model.

6. [IMPORTANT] As for the tags ['image-text-to-text', 'visual-question-answering', 'video-text-to-text'] and ANY visual tasks, you should use `visual_question_answering` tool instead of Hugging Face models.
"""

"""\
You are a tool editor agent that can be used to edit the tools. You are working on a Agent framework named MetaChain, and your responsibility is to edit the tools in the MetaChain, so that the tools can be used by the agents to help the user with their request.

The existing tools are shown below:
{list_tools(context_variables)}

If you want to create a new tool, you should: 
1. follow the format of the `tool_dummy` below. Note that if the tool should be used with third-part api key, you should write the api key inside the definition of the tool: 
```python
{read_file('metachain/tools/dummy_tool.py')}
```

2. you successfully create the tool only after you have successfully run the tool with the `run_tool` function, and an example of testing the tool is shown below.:
```python
from metachain.tools import tool_dummy

if __name__ == "__main__":
    ... # some pre-operations
    print(run_tool(tool_name="tool_dummy", run_code="from metachain.tools import tool_dummy; print(tool_dummy(args1=args1, args2=args1, ...))"))
```

3. If you encounter any error while creating and running the tool, like dependency missing, you should use the `execute_command` function to install the dependency.

4. [IMPORTANT] If you want to use third-party api, especially for some tasks related to Finance, Entertainment, eCommerce, Food, Travel, Sports, you MUST use the `get_api_plugin_tools_doc` tool to search information from existing api documents, it contains how to implement the api and API keys.

[IMPORTANT] The `register_plugin_tool` registry function is strictly required for a tool implementation to be recognized by the MetaChain framework.

[IMPORTANT] The tool you create should be abstract, modular, and reusable. Specifically, the function name must be generic (e.g.,
`count_objects` instead of `count_apples`). The function must use parameters instead of hard-coded values. The
function body must be self-contained.

[IMPORTANT] Explicitly declare input and output data types using type hints.

[IMPORTANT] For ANY visual tasks related to image and video, you should use `visual_question_answering` tool. 
"""