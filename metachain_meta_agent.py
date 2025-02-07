from constant import DOCKER_WORKPLACE_NAME
from metachain.io_utils import read_yaml_file, get_md5_hash_bytext, read_file
from metachain.workflow import Graph, FlowEngine, meta_agent
from metachain.environment.utils import setup_metachain
from metachain.types import Response
from metachain import MetaChain
from metachain.util import ask_text, single_select_menu, print_markdown, debug_print, UserCompleter
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from rich.progress import Progress, SpinnerColumn, TextColumn
import json
import argparse
from datetime import datetime
from metachain.agents.meta_agent import tool_editor, agent_editor
from metachain.tools.meta.edit_tools import list_tools
from metachain.tools.meta.edit_agents import list_agents
from loop_utils.font_page import MC_LOGO, version_table, NOTES, GOODBYE_LOGO
from rich.live import Live
from metachain.environment.docker_env import DockerEnv, DockerConfig, check_container_ports
from metachain.environment.browser_env import BrowserEnv
from metachain.environment.markdown_browser import RequestsMarkdownBrowser
from evaluation.utils import update_progress, check_port_available, run_evaluation, clean_msg
import os
import os.path as osp
from metachain.agents import get_system_triage_agent
from metachain.logger import LoggerManager, MetaChainLogger 
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from rich.columns import Columns
from rich.text import Text
from rich.panel import Panel
from metachain.agents.meta_agent.agent_former import get_agent_former_agent 
from metachain.agents.meta_agent.tool_editor import get_tool_editor_agent
from metachain.agents.meta_agent.agent_creator import get_agent_creator_agent
import re
from metachain.agents.meta_agent.form_complie import parse_agent_form

def get_args(): 
    parser = argparse.ArgumentParser(description="working@tjb-tech")
    parser.add_argument('--container_name', type=str, default='gpu_test')
    parser.add_argument('--model', type=str, default='gpt-4o-2024-08-06')
    parser.add_argument('--test_pull_name', type=str, default='test_pull_1010')
    parser.add_argument('--debug', action='store_true', default=False)
    parser.add_argument('--port', type=int, default=12350)
    parser.add_argument('--git_clone', action='store_true', default=False)
    parser.add_argument('--task_cfg', type=str, default='benchmarks/case_study/finance_agent/case_finance_agent_single.yaml')
    args = parser.parse_args()
    return args
def get_config(args):
    container_name = args.container_name
    
    port_info = check_container_ports(container_name)
    port = args.port
    if port_info:
        port = port_info[0]
    else:
        # while not check_port_available(port):
        #     port += 1
        # 使用文件锁来确保端口分配的原子性
        import filelock
        lock_file = os.path.join(os.getcwd(), ".port_lock")
        lock = filelock.FileLock(lock_file)
        
        with lock:
            port = args.port
            while not check_port_available(port):
                port += 1
                print(f'{port} is not available, trying {port+1}')
            # 立即标记该端口为已使用
            with open(os.path.join(os.getcwd(), f".port_{port}"), 'w') as f:
                f.write(container_name)
    local_root = os.path.join(os.getcwd(), f"workspace_meta_showcase", f"showcase_{container_name}")
    os.makedirs(local_root, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    docker_config = DockerConfig(
        workplace_name=DOCKER_WORKPLACE_NAME,
        container_name=container_name,
        communication_port=port,
        conda_path='/root/miniconda3',
        local_root=local_root,
        git_clone=args.git_clone,
        test_pull_name=args.test_pull_name,
        task_name = "meta_agent_" + timestamp
    )
    return docker_config
def create_environment(docker_config: DockerConfig):
    """
    1. create the code environment
    2. create the web environment
    3. create the file environment
    """
    code_env = DockerEnv(docker_config)
    code_env.init_container()
    
    web_env = BrowserEnv(browsergym_eval_env = None, local_root=docker_config.local_root, workplace_name=docker_config.workplace_name)
    file_env = RequestsMarkdownBrowser(viewport_size=1024 * 5, local_root=docker_config.local_root, workplace_name=docker_config.workplace_name, downloads_folder=os.path.join(docker_config.local_root, docker_config.workplace_name, "downloads"))
    
    return code_env, web_env, file_env
def extract_agents_content(text):
    pattern = r'(<agents>.*?</agents>)'
    # re.DOTALL 让 . 也能匹配换行符
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1)
    return None
def main(args):
    print('\033[s\033[?25l', end='')  # Save cursor position and hide cursor
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True  # 这会让进度条完成后消失
    ) as progress:
        task = progress.add_task("[cyan]Initializing...", total=None)
        
        progress.update(task, description="[cyan]Initializing config...[/cyan]\n")
        docker_config = get_config(args)
        
        progress.update(task, description="[cyan]Setting up logger...[/cyan]\n")
        log_path = osp.join("casestudy_results", 'logs', f'agent_{args.container_name}_{args.model}.log')
        os.makedirs(osp.dirname(log_path), exist_ok=True)
        LoggerManager.set_logger(MetaChainLogger(log_path = log_path))
        
        progress.update(task, description="[cyan]Creating environment...[/cyan]\n")
        code_env, web_env, file_env = create_environment(docker_config)
        
        progress.update(task, description="[cyan]Setting up metachain...[/cyan]\n")
        setup_metachain(workplace_name=docker_config.workplace_name, env=code_env)
    
    context_variables = {"working_dir": docker_config.workplace_name, "code_env": code_env, "web_env": web_env, "file_env": file_env}
    task_cfg = read_yaml_file(args.task_cfg)
    
    # generate agent form
    client = MetaChain(LoggerManager.get_logger())
    agent_former = get_agent_former_agent(args.model)
    messages = [
        {"role": "user", "content": task_cfg["requirements"] + """
Directly output the form in the XML format without ANY other text.
"""}
    ]
    response = client.run(agent_former, messages, context_variables)
    output_xml_form = response.messages[-1]["content"]
    messages.extend(response.messages)


    MAX_RETRY = 3
    for i in range(MAX_RETRY):
        try:
            output_xml_form = extract_agents_content(output_xml_form)
            assert output_xml_form is not None, "No the XML form should be found in the output with the tag <agents>...</agents>."
            agent_form = parse_agent_form(output_xml_form)
            break
        except Exception as e:
            print(f"Error parsing XML to agent form: {e}. Retry {i+1}/{MAX_RETRY}")
            messages.append({"role": "user", "content": f"Error parsing XML to agent form: {e}\nNote that there are some special restrictions for creating agent form, please try again."})
            response = client.run(agent_former, messages, context_variables)
            output_xml_form = response.messages[-1]["content"]
            messages.extend(response.messages)
    print(output_xml_form)
    tool_editor_agent = get_tool_editor_agent(args.model)
    def case_resolved(task_response: str, context_variables: dict): 
        """
        Use this tools when the desired tool is created and tested successfully. You can NOT use this tool if the tool is not created or tested successfully by running the tool.

        Args: 
            task_response: the response of creating the tool which contains the completion status of the tool.
        """
        return f"Case resolved. The desired tool is created and tested successfully. Details: {task_response}"
    def case_not_resolved(task_response: str, context_variables: dict):
        """
        Use this tools when you encounter irresistible errors after trying your best with multiple attempts for creating the desired tool. You can NOT use this tool before you have tried your best.

        Args: 
            task_response: the reason why the tool is not created or tested successfully.
        """
        return f"Case not resolved. The desired tool is not created or tested successfully. Details: {task_response}"
    tool_editor_agent.functions.extend([case_resolved, case_not_resolved])

    agents = agent_form.agents
    for agent in agents:
        if len(agent.tools.new) > 0:
            new_tools = []
            for idx, tool in enumerate(agent.tools.new):
                new_tools.append(f"{idx+1}. Tool name: {tool.name}, Tool description: {tool.description}")
            new_tools_str = "\n".join(new_tools)
            messages.append({"role": "user", "content": f"""\
Your task is to create a list of new tools for me, the tools are:
{new_tools_str}

Please create these new tools for me, note that you can NOT stop util you have created all the tools and tested them using `run_tool` successfully. 

If EVERY tool is created and tested successfully, you can stop and output "Case resolved". Otherwise, you should continue to create the tools. After you have tried your best, you can output "Case not resolved" and give the reason why the tool is not created or tested successfully.

[IMPORTANT] EVERY tool MUST be tested successfully by running the tool using `run_tool` before you stop.
"""})
            response = client.run(tool_editor_agent, messages, context_variables)
            content = response.messages[-1]["content"]
            for i in range(MAX_RETRY):
                if content.startswith("Case resolved"):
                    break
                messages.append({"role": "user", "content": f"""\
Your task is to create a list of new tools for me, the tools are:
{new_tools_str}

Please create these new tools for me, note that you can NOT stop util you have created all the tools and tested them using `run_tool` successfully.
The last attempt failed with the following error: {content}, please try again to create the tools.
"""})
                response = client.run(tool_editor_agent, messages, context_variables)
                content = response.messages[-1]["content"]
            if i == MAX_RETRY:
                return f"The desired tool is not created or tested successfully with {MAX_RETRY} attempts."
    
    # create agents: 
    agent_creator_agent = get_agent_creator_agent(args.model)
    def case_resolved(task_response: str, context_variables: dict): 
        """
        Use this tools when the desired agent(s) is created and tested successfully. You can NOT use this tool if the agent(s) is not created or tested successfully by running the agent(s).
        """
        return f"Case resolved. The desired agent(s) is created and tested successfully.    : {task_response}"
    def case_not_resolved(task_response: str, context_variables: dict):
        """
        Use this tools when you encounter irresistible errors after trying your best with multiple attempts for creating the desired agent(s). You can NOT use this tool before you have tried your best.
        """
        return f"Case not resolved. The desired agent(s) is not created or tested successfully. Details: {task_response}"
    agent_creator_agent.functions.extend([case_resolved, case_not_resolved])
    messages.append({"role": "user", "content": f"""\
The user's request to create agent(s) is: {task_cfg["requirements"]}
Given the completed agent form with XML format: {output_xml_form}
After previous attempts, you have created new tools that required by the desired agent(s). 

Your task is to create the desired agent(s) for me, note that you may create ONE single agent or multiple agents connected by orchestrator agent.

After you have created the agent(s), you should test the agent(s) by running the agent(s) using `run_agent` tool to complete the user's task: 
{task_cfg["task"]}

Note that you can NOT stop util you have created the agent(s) and tested it successfully.
"""})
    response = client.run(agent_creator_agent, messages, context_variables)
    content = response.messages[-1]["content"]
    for i in range(MAX_RETRY):
        if content.startswith("Case resolved"):
            break
        messages.append({"role": "user", "content": f"""\
The user's request to create agent(s) is: {task_cfg["requirements"]}
Given the completed agent form with XML format: {output_xml_form}
After previous attempts, you have created new tools that required by the desired agent(s). 

Your task is to create the desired agent(s) for me, note that you may create ONE single agent or multiple agents connected by orchestrator agent.

After you have created the agent(s), you should test the agent(s) by running the agent(s) using `run_agent` tool to complete the user's task: 
{task_cfg["task"]} 

Note that you can NOT stop util you have created the agent(s) and tested it successfully.
The last attempt failed with the following error: {content}, please try again to create the desired agent(s).
"""})
        response = client.run(agent_creator_agent, messages, context_variables)
        content = response.messages[-1]["content"]
    if i == MAX_RETRY:
        return f"The desired agent(s) is not created or tested successfully with {MAX_RETRY} attempts."


if __name__ == "__main__":
    args = get_args()
    main(args)