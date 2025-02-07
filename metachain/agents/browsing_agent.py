from metachain.types import Agent
from metachain.registry import register_agent
from browsergym.core.action.highlevel import HighLevelActionSet
from metachain.util import function_to_json
import gymnasium as gym
import browsergym.miniwob  # register miniwob tasks as gym environments
import importlib
import json
from functools import wraps
from typing import Callable, Union  
from metachain.environment.browser_env import BrowserEnv
import inspect
from metachain.types import Result
from browsergym.utils.obs import flatten_axtree_to_str
def get_error_prefix(last_browser_action: str) -> str:
    return f'IMPORTANT! Last action is incorrect:\n{last_browser_action}\nThink again with the current observation of the page.\n'
def wrap_browser_action(action_func: Callable, env: BrowserEnv) -> Callable:
    """
    包装浏览器动作函数，使其能与环境交互
    
    Args:
        action_func: 原始的浏览器动作函数
        
    Returns:
        包装后的函数，可以与环境交互
    """
    @wraps(action_func)
    def wrapper(*args, **kwargs) -> Union[Result, str]:
        error_prefix = ""
        try:
            # 执行动作
            # action = action_func(*args, **kwargs)
            action_str = f"{action_func.__name__}({', '.join([f'{repr(v)}' for k, v in kwargs.items()])})"
            
            # 与环境交互
            obs = env.step(action_str)
            
            # 返回观察结果
            obs_dict = dict(
            content=obs['text_content'],  # text content of the page
            url=obs.get('url', ''),  # URL of the page
            screenshot=obs.get('screenshot', None),  # base64-encoded screenshot, png
            open_pages_urls=obs.get('open_pages_urls', []),  # list of open pages
            active_page_index=obs.get(
                'active_page_index', -1
            ),  # index of the active page
            dom_object=obs.get('dom_object', {}),  # DOM object
            axtree_object=obs.get('axtree_object', {}),  # accessibility tree object
            extra_element_properties=obs.get('extra_element_properties', {}),
            focused_element_bid=obs.get(
                'focused_element_bid', None
            ),  # focused element bid
            last_browser_action=obs.get(
                'last_action', ''
            ),  # last browser env action performed
            last_browser_action_error=obs.get('last_action_error', ''),
            error=True if obs.get('last_action_error', '') else False,  # error flag
        )
        except Exception as e:
            obs_dict = dict(
            content=str(e),
            screenshot='',
            error=True,
            last_browser_action_error=str(e),
            )

        if obs_dict['error']:
            # add error recovery prompt prefix
            error_prefix = get_error_prefix(obs_dict['last_browser_action'])
            # self.error_accumulator += 1
            # if self.error_accumulator > 5:
            #     return MessageAction('Too many errors encountered. Task failed.')

        cur_url = obs_dict['url']

        try:
            cur_axtree_txt = flatten_axtree_to_str(
                obs_dict['axtree_object'],
                extra_properties=obs_dict['extra_element_properties'],
                with_clickable=True,
                filter_visible_only=True,
            )
        except Exception as e:
            print(
                'Error when trying to process the accessibility tree: %s', e
            )
            return 'Error encountered when browsing.'
        ret_value = f"""\
{error_prefix}

# Current Page URL:
{cur_url}

# Current Accessibility Tree:
{cur_axtree_txt}

Here is an example with chain of thought of a valid action when clicking on a button:
"
In order to accomplish my goal I need to click on the button with bid 12
```click("12")```
"
""".strip()
        return Result(
            value=ret_value,
            image=obs_dict['screenshot'], 
        )
    
    # 保留原函数的签名和文档
    wrapper.__signature__ = inspect.signature(action_func)
    wrapper.__doc__ = action_func.__doc__
    
    return wrapper
@register_agent(name = "Browsing Agent", func_name="get_browsing_agent")
def get_browsing_agent(model: str):
    env = BrowserEnv()
    demo_mode = "off"
    action_set = HighLevelActionSet(
                subsets=["chat", "nav", "bid"],  # define a subset of the action space
                # subsets=["chat", "bid", "coord", "infeas"] # allow the agent to also use x,y coordinates
                strict=False,  # less strict on the parsing of the actions
                multiaction=False,  # does not enable the agent to take multiple actions at once
                demo_mode=demo_mode,  # add visual effects
            )
    func_list = [act for act in action_set.action_set.keys()]
    func_module = importlib.import_module("browsergym.core.action.functions")
    func_list = [getattr(func_module, func) for func in func_list]
    wrap_func_list = [wrap_browser_action(func, env) for func in func_list]
    def instructions(context_variables):
        goal = context_variables.get("goal", "")
        action_space = action_set.describe(with_long_description=False, with_examples=True)
        return \
f"""Review the current state of the page and all other information to find the best
possible next action to accomplish your goal. Your answer will be interpreted
and executed by a program, make sure to follow the formatting instructions.

# Goal:
{goal}

# Action Space
{action_space}
"""
    return Agent(
        name="Browsing Agent",
        model=model,
        instructions=instructions,
        functions=wrap_func_list
    )
