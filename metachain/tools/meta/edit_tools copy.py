from metachain.registry import registry
from metachain.environment import LocalEnv, DockerEnv
from typing import Union
from metachain.tools.terminal_tools import (
    create_file, 
    create_directory, 
    run_python, 
    )
from metachain.registry import register_tool

from metachain.io_utils import print_stream
import json
def get_metachain_path(env: Union[LocalEnv, DockerEnv]) -> str: 
    result = env.run_command('pip show metachain')
    if result['status'] != 0:
        raise Exception("Failed to list tools. Error: " + result['result'])
    stdout = result['result']
    for line in stdout.split('\n'):
        if line.startswith('Editable project location:'):
            path = line.split(':', 1)[1].strip()
            return path
    raise Exception("Failed to list tools. The MetaChain is not installed in editable mode.")

@register_tool("list_tools")
def list_tools(context_variables): 
    """
    List all plugin tools in the MetaChain.
    Returns:
        A list of information of all plugin tools including name, args, docstring, body, return_type, file_path.
    """
    env: Union[LocalEnv, DockerEnv] = context_variables.get("code_env", LocalEnv())
    try:
        path = get_metachain_path(env)
    except Exception as e:
        return "Failed to list tools. Error: " + str(e)
    python_code = '"from metachain.registry import registry; import json; print(\\"TOOL_LIST_START\\"); print(json.dumps(registry.display_plugin_tools_info, indent=4)); print(\\"TOOL_LIST_END\\")"'
    list_tools_cmd = f"cd {path} && DEFAULT_LOG=False python -c {python_code}"
    result = env.run_command(list_tools_cmd)
    if result['status'] != 0:
        return "Failed to list tools. Error: " + result['result']
    try:
        output = result['result']
        start_marker = "TOOL_LIST_START"
        end_marker = "TOOL_LIST_END"
        start_idx = output.find(start_marker) + len(start_marker)
        end_idx = output.find(end_marker)
        
        if start_idx == -1 or end_idx == -1:
            return "Failed to parse tool list: markers not found"
            
        json_str = output[start_idx:end_idx].strip()
        return json_str
    except Exception as e:
        return f"Failed to process output: {str(e)}"
    # return result['result']

@register_tool("create_tool")
def create_tool(tool_name: str, tool_code: str, context_variables): 
    """
    Create a plugin tool.
    Args:
        tool_name: The name of the tool.
        tool_code: The code of creating the tool. (You should strictly follow the format of the template given to you to create the tool.)
    Returns:
        A string representation of the result of the tool creation.
    """
    if tool_name == "visual_question_answering":
        return "The tool `visual_question_answering` is not allowed to be modified."
    env: Union[LocalEnv, DockerEnv] = context_variables.get("code_env", LocalEnv())
    try:
        path = get_metachain_path(env)
    except Exception as e:
        return "Failed to list tools. Error: " + str(e)
    
    tools_dir = path + "/metachain/tools"
    try:  
        msg = create_file(tools_dir + "/" + tool_name + ".py", tool_code, context_variables)
        if msg.startswith("Error creating file:"):
            return "Failed to create tool. Error: " + msg
        return "Successfully created tool: " + tool_name + " in " + tools_dir + "/" + tool_name + ".py"
    except Exception as e:
        return "Failed to create tool. Error: " + str(e)

def tool_exists(tool_name: str, context_variables):
    try:
        list_res = list_tools(context_variables)
        tool_dict = json.loads(list_res)
        if tool_name not in tool_dict.keys():
            return False, tool_dict
        return True, tool_dict
    except Exception as e:
        return "Before deleting a tool, you should list all tools first. But the following error occurred: " + str(e), None

@register_tool("delete_tool")
def delete_tool(tool_name: str, context_variables): 
    """
    Delete a plugin tool.
    Args:
        tool_name: The name of the tool to be deleted.
    Returns:
        A string representation of the result of the tool deletion.
    """
    env: Union[LocalEnv, DockerEnv] = context_variables.get("code_env", LocalEnv())
    # try:
    #     exist_flag, tool_dict = tool_exists(tool_name, context_variables)
    #     if isinstance(exist_flag, str):
    #         return "Before deleting a tool, you should list all tools first. But the following error occurred: " + exist_flag
    #     if not exist_flag:
    #         return f"The tool `{tool_name}` does not exist."
    # except Exception as e:
    #     return "Before deleting a tool, you should list all tools first. But the following error occurred: " + str(e)
    list_res = list_tools(context_variables)
    tool_dict = json.loads(list_res)
    try:
        tool_path = tool_dict[tool_name]['file_path']
    except KeyError: 
        return "The tool `" + tool_name + "` does not exist."
    except Exception as e:
        return "Error: " + str(e)
    try:
        result = env.run_command(f"rm {tool_path}")
        if result['status'] != 0:
            return f"Failed to delete tool: `{tool_name}`. Error: " + result['result']
        return f"Successfully deleted tool: `{tool_name}`."
    except Exception as e:
        return f"Failed to delete tool: `{tool_name}`. Error: " + str(e)

@register_tool("update_tool")
def update_tool(tool_name: str, tool_code: str, context_variables): 
    """
    Update an existing plugin tool.
    Args:
        tool_name: The name of the tool to be updated.
        tool_code: The code of the tool to be updated.
    Returns:
        A string representation of the result of the tool update.
    """
    env: Union[LocalEnv, DockerEnv] = context_variables.get("code_env", LocalEnv())
    # try:
    #     exist_flag, tool_dict = tool_exists(tool_name, context_variables)
    #     if isinstance(exist_flag, str):
    #         return "Before deleting a tool, you should list all tools first. But the following error occurred: " + exist_flag
    #     if not exist_flag:
    #         return f"The tool `{tool_name}` does not exist."
    # except Exception as e:
    #     return "Before updating a tool, you should list all tools first. But the following error occurred: " + str(e)
    list_res = list_tools(context_variables)
    tool_dict = json.loads(list_res)
    try:
        tool_path = tool_dict[tool_name]['file_path']
    except KeyError: 
        return "The tool `" + tool_name + "` does not exist."
    except Exception as e:
        return "Error: " + str(e)
    
    try: 
        msg = create_file(tool_path, tool_code, context_variables)
        if msg.startswith("Error creating file:"):
            return "Failed to update tool. Error: " + msg
        return "Successfully updated tool: " + tool_name + " in " + tool_path
    except Exception as e:
        return "Failed to update tool. Error: " + str(e)


@register_tool("test_tool")
def test_tool(tool_name: str, test_code: str, context_variables): 
    env: Union[LocalEnv, DockerEnv] = context_variables.get("code_env", LocalEnv())
    try:
        path = get_metachain_path(env)
    except Exception as e:
        return "Failed to get the path of the MetaChain. Error: " + str(e)
    # try:
    #     exist_flag, tool_dict = tool_exists(tool_name, context_variables)
    #     if isinstance(exist_flag, str):
    #         return "Before deleting a tool, you should list all tools first. But the following error occurred: " + exist_flag
    #     if not exist_flag:
    #         return f"The tool `{tool_name}` does not exist."
    # except Exception as e:
    #     return "Before testing a tool, you should list all tools first. But the following error occurred: " + str(e)
    
    test_dir = path + "/test_tools"

    try: 
        msg = create_directory(test_dir, context_variables)
        if msg.startswith("Error creating directory:"):
            return "Failed to create the test directory. Error: " + msg
    except Exception as e:
        return "Failed to create the test directory. Error: " + str(e)
    
    test_file_path = test_dir + "/" + "test_" + tool_name + ".py"
    try:
        msg = create_file(test_file_path, test_code, context_variables)
        if msg.startswith("Error creating file:"):
            return "Failed to create the test file. Error: " + msg
    except Exception as e:
        return "Failed to create the test file. Error: " + str(e)
    
    try:
        result = run_python(context_variables, test_file_path, cwd=path, env_vars={"DEFAULT_LOG": "False"})
        if "Exit code: 0" not in result:
            return "Failed to test the tool. The test case is not correct. The result is: " + result
        return f"The result is of the tool `{tool_name}`: \n{result}"
    except Exception as e:
        return "Failed to test the tool. Error: " + str(e)

if __name__ == "__main__":
    print(list_tools({}))
