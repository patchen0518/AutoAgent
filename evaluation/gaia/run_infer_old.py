from metachain.environment.docker_container import init_container
import argparse
from constant import DOCKER_WORKPLACE_NAME
from datasets import load_dataset
import huggingface_hub
from metachain import MetaChain
from metachain.logger import MetaChainLogger, LoggerManager
from evaluation.utils import make_metadata, prepare_dataset, update_progress, check_port_available, run_evaluation, clean_msg
from evaluation.types import EvalMetadata, EvalOutput
import metachain.agents as agenthub
import os.path as osp
import pandas as pd
import asyncio
import re
import os
import shutil
from metachain.registry import registry
from evaluation.gaia.scorer import question_scorer
import json
# from metachain.util import run_command_in_container
from metachain.environment.docker_env import DockerEnv, DockerConfig, check_container_ports, check_container_exist, check_container_running
from metachain.environment.browser_env import BrowserEnv
from metachain.environment.markdown_browser import RequestsMarkdownBrowser
from metachain.types import Response
from metachain.util import function_to_json
from metachain.main import run_in_client
import subprocess
DATASET_CACHE_DIR = osp.join(osp.dirname(__file__), 'data')
# Note: You should run this script in the root directory of the project metachain
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--container_name', type=str, default='gaia_test')
    parser.add_argument('--model', type=str, default='gpt-4o-2024-08-06')
    parser.add_argument('--git_clone', action='store_true', default=False)
    parser.add_argument('--setup_package', type=str, default=None)
    parser.add_argument('--test_pull_name', type=str, default='main')
    parser.add_argument('--debug', action='store_true', default=False)
    # metadata
    parser.add_argument('--agent_func', type=str, default='get_system_triage_agent')
    parser.add_argument('--eval_note', type=str, default=None)
    parser.add_argument('--eval_output_dir', type=str, default='./evaluation_results')
    parser.add_argument('--data_split', type=str, default=None)
    # gaia level
    parser.add_argument('--level', type=str, default='1')
    parser.add_argument('--eval_n_limit', type=int, default=None)
    parser.add_argument('--port', type=int, default=12345)
    parser.add_argument('--eval_num_workers', type=int, default=1)
    args = parser.parse_args()
    return args

def get_config(metadata: EvalMetadata, instance_id: str):
    container_name = metadata.container_name+f'_{instance_id}'
    
    port_info = check_container_ports(container_name)
    port = metadata.port
    if port_info:
        port = port_info[0]
    else:
        while not check_port_available(port):
            port += 1
    local_root = os.path.join(os.getcwd(), f"workspace_gaia_whole", f"gaia_eval_{instance_id}")
    os.makedirs(local_root, exist_ok=True)
    docker_config = DockerConfig(
        workplace_name=DOCKER_WORKPLACE_NAME,
        container_name=container_name,
        communication_port=port,
        conda_path='/root/miniconda3',
        local_root=local_root,
    )
    return docker_config

def process_instance(
    instance: pd.Series,
    metadata: EvalMetadata,
    logger: MetaChainLogger,
) -> EvalOutput:
    
    docker_config = get_config(metadata, instance_id=instance['instance_id'])

    code_env, web_env, file_env = create_environment(docker_config)
    local_workplace = code_env.local_workplace
    docker_workplace = code_env.docker_workplace

    # Setup the logger properly, so you can run multi-processing to parallelize the evaluation
    logger.info(f'Starting evaluation for instance {instance["instance_id"]}.')

    if instance['file_name'] != '':
        assert metadata.data_split is not None
        src_file = os.path.join(
            DATASET_CACHE_DIR, '2023', metadata.data_split, instance['file_name']
        )
        assert os.path.exists(src_file)
        extension_name = instance['file_name'].split('.')[-1]
        dest_file = os.path.join(local_workplace, f'file.{extension_name}')
        shutil.copy(src_file, dest_file)
        file_name = dest_file.split('/')[-1]
    else:
        dest_file = None
    

    # Prepare instruction
    instruction = f"{instance['Question']}\n"
    logger.info(f'Instruction: {instruction}')
    if dest_file:
        instruction += f"\n\nThe mentioned file is provided in the workspace at: {osp.join(docker_workplace, file_name)}"

    instruction += 'IMPORTANT: You should ONLY interact with the environment provided to you AND NEVER ASK FOR HUMAN HELP.\n'
    instruction += 'Please encapsulate your final answer (answer ONLY) within <solution> and </solution>.\n'
    instruction += (
        'For example: The answer to the question is <solution> 42 </solution>.\n'
    )
    
    logger.info(f'Instruction:\n{instruction}')

    system_triage_agent = registry.agents[metadata.agent_func](model=metadata.model, file_env=file_env, web_env=web_env, code_env=code_env)
    messages = [
        {
            'role': 'user',
            'content': instruction
        }
    ]

    context_variables = {}
    # Here's how you can run the agent (similar to the `main` function) and get the final task state
    response: Response | None = asyncio.run(
        run_in_client(
            agent=system_triage_agent,
            messages=messages,
            context_variables = context_variables, 
            logger=logger
        )
    )
    messages.extend(response.messages)
    # save messages to a file
    messages_file = osp.join(metadata.eval_output_dir, f"gaia_{instance['instance_id']}", f'messages_{metadata.agent_func.replace("get_", "")}.json')
    os.makedirs(osp.dirname(messages_file), exist_ok=True)
    messages = clean_msg(messages)
    with open(messages_file, 'w', encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=4)
    # ======= Attempt to evaluate the agent's edits =======
    # If you are working on simpler benchmark that only evaluates the final model output (e.g., in a MessageAction)
    # You can simply get the LAST `MessageAction` from the returned `state.history` and parse it for evaluation.

    if response is None:
        raise ValueError('Response should not be None.')

    model_answer_raw = response.messages[-1]['content']

    # attempt to parse model_answer
    model_answer = re.findall(r'<solution>(.*?)</solution>', model_answer_raw)
    if len(model_answer) == 0:
        logger.info(f'Failed to parse model answer: {model_answer_raw}', title='WARNING', color='yellow')
        model_answer = model_answer_raw
    else:
        model_answer = model_answer[0]

    logger.info(
        f'Final message: {model_answer} | Ground truth: {instance["Final answer"]}',
        title='INFO', color='green'
    )
    score = question_scorer(
        model_answer=model_answer, ground_truth=instance['Final answer']
    )
    test_result = {
        'score': score,
        'model_answer_raw': model_answer_raw,
        'model_answer': model_answer,
        'ground_truth': instance['Final answer'],
    }


    # Save the output
    output = EvalOutput(
        instance_id=instance['instance_id'],
        instance=instance.to_dict(),
        instruction=instance['Question'],
        metadata=metadata,
        messages=messages,
        test_result=test_result,
    )
    return output

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
def main(args):
    metadata: EvalMetadata = make_metadata(
        model=args.model,
        dataset_name="gaia",
        agent_func=args.agent_func,
        eval_note=args.eval_note,
        eval_output_dir=args.eval_output_dir,
        data_split=args.data_split,
        details={'gaia-level': args.level},
        port=args.port,
        container_name=args.container_name,
    )
    log_path = osp.join(metadata.eval_output_dir, 'logs', f'agent_{metadata.model}.log')
    LoggerManager.set_logger(MetaChainLogger(log_path))

    dataset = load_dataset('gaia-benchmark/GAIA', args.level)
    huggingface_hub.snapshot_download(
        'gaia-benchmark/GAIA',
        repo_type='dataset',
        local_dir=DATASET_CACHE_DIR,
    )
    gaia_tests = dataset[metadata.data_split].to_pandas()
    gaia_tests.rename(columns={'task_id': 'instance_id'}, inplace=True)
    
    output_file = osp.join(metadata.eval_output_dir, 'output.jsonl')
    prepared_dataset = prepare_dataset(gaia_tests, output_file, args.eval_n_limit)

    run_evaluation(
        dataset=prepared_dataset,
        metadata=metadata,
        output_file=output_file,
        num_workers=args.eval_num_workers,
        process_instance_func=process_instance,
    )



if __name__ == "__main__":
    args = get_args()
    main(args)
    # print(check_container_exist('gaia_lite_eval_c61d22de-5f6c-4958-a7f6-5e9707bd3466'))