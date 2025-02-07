current_dir=$(dirname "$(readlink -f "$0")")

cd $current_dir
export DOCKER_WORKPLACE_NAME=workplace
export EVAL_MODE=True
export DEBUG=True
export BASE_IMAGES=tjb-gaia-bookworm:v2
export COMPLETION_MODEL=claude-3-5-sonnet-20241022
# export COMPLETION_MODEL=gpt-4o-2024-08-06
export MC_MODE=False

task_cfg="benchmarks/case_study/math_workflow/majority_voting(paralizing).yaml"
# task_cfg="benchmarks/case_study/math_workflow/condition_mining(evaluator-optimizer).yaml"

python metachain_meta_workflow.py --container_name nl2agent_showcase --model ${COMPLETION_MODEL} --test_pull_name test_pull_0111 --debug --port 12350 --git_clone --task_cfg ${task_cfg}
# python /Users/tangjiabin/Documents/reasoning/metachain/test_gaia_tool.py