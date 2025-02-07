current_dir=$(dirname "$(readlink -f "$0")")

cd $current_dir
export DOCKER_WORKPLACE_NAME=workplace
export EVAL_MODE=True
export DEBUG=True
export BASE_IMAGES=tjbtech1/gaia-bookworm:v2
export COMPLETION_MODEL=claude-3-5-sonnet-20241022
# export COMPLETION_MODEL=gpt-4o-2024-08-06
export DEBUG=False
export MC_MODE=True

python metachain_loop.py --container_name quick_start --model ${COMPLETION_MODEL} --test_pull_name test_pull_1225 --debug --port 12350 --git_clone
# python /Users/tangjiabin/Documents/reasoning/metachain/test_gaia_tool.py
