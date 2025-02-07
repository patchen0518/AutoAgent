from metachain.types import Agent
from metachain.tools import (
    gen_code_tree_structure, execute_command, read_file, create_file, write_file, list_files, create_directory, run_python, code_rag, case_resolved, get_api_plugin_tools_doc
)
from metachain.util import make_message, make_tool_message
from metachain.registry import register_agent
def examples(context_variables):
    working_dir = context_variables.get("working_dir", None)
    examples_list = []
    examples_list.extend(make_message('user', "Create a list of numbers from 1 to 10, and display them in a web page at port 5000."))
    examples_list.extend(make_message('assistant', "I should first use create_file to write the python code into a file named 'app.py' for starting a web server"))
    examples_list.extend(make_tool_message(create_file, {'path': f"/{working_dir}/metachain/app.py", 
            'content': """
from flask import Flask
app = Flask(__name__)

@app.route('/')
def index():
    numbers = list(range(1, 11))
    return str(numbers)

if __name__ == '__main__':
    app.run(port=5000)"""}, f"File created at: /{working_dir}/metachain/app.py"))
    examples_list.extend(make_message('assistant', 'I have created a Python file `app.py` that will display a list of numbers from 1 to 10 when you run it. Let me run the Python file for you using `run_python`'))
    examples_list.extend(make_tool_message(run_python, {'code_path': f"/{working_dir}/metachain/app.py"}, f"""
Traceback (most recent call last):
  File "/{working_dir}/metachain/app.py", line 2, in <module>
    from flask import Flask
ModuleNotFoundError: No module named 'flask'"""))
    examples_list.extend(make_message('assistant', "It seems that Flask is not installed. Let me install Flask for you using `execute_command` by the command: pip install flask"))
    examples_list.extend(make_tool_message(execute_command, {'command': 'pip install flask'}, """Defaulting to user installation because normal site-packages is not writeable
Collecting flask
  Using cached flask-3.0.3-py3-none-any.whl (101 kB)
Collecting blinker>=1.6.2
  Using cached blinker-1.7.0-py3-none-any.whl (13 kB)
Collecting Werkzeug>=3.0.0
  Using cached werkzeug-3.0.2-py3-none-any.whl (226 kB)
Collecting click>=8.1.3
  Using cached click-8.1.7-py3-none-any.whl (97 kB)
Collecting itsdangerous>=2.1.2
  Using cached itsdangerous-2.2.0-py3-none-any.whl (16 kB)
Requirement already satisfied: Jinja2>=3.1.2 in /home/openhands/.local/lib/python3.10/site-packages (from flask) (3.1.3)
Requirement already satisfied: MarkupSafe>=2.0 in /home/openhands/.local/lib/python3.10/site-packages (from Jinja2>=3.1.2->flask) (2.1.5)
Installing collected packages: Werkzeug, itsdangerous, click, blinker, flask
Successfully installed Werkzeug-3.0.2 blinker-1.7.0 click-8.1.7 flask-3.0.3 itsdangerous-2.2.0"""))
    examples_list.extend(make_message('assistant', "Now that Flask is installed, let me run the Python file again using `run_python`"))
    examples_list.extend(make_tool_message(run_python, {'code_path': f"/{working_dir}/metachain/app.py"}, """* Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit"""))
    examples_list.extend(make_message('assistant', """The server is running on port 5000 with PID 124. You can access the list of numbers by visiting http://127.0.0.1:5000. Your task is completed."""))
    return examples_list

@register_agent(name = "Programming Agent", func_name="get_programming_agent")
def get_programming_agent(model: str):
    def instructions(context_variables):
      working_dir = context_variables.get("working_dir", None)
      ret_instructions =  \
  f"""You are a programmer working on an agent project named 'metachain' whose path is /{working_dir}/metachain.

  Your can leverage your capabilities by using the specific functions listed below:

  1. Creating project structures based on the user requirement using function `create_directory`.
  2. Writing clean, efficient, and well-documented code using function `create_file` and `write_file`.
  3. You must run python scripts using function `run_python` rather than using the `execute_command` function.
  4. Exam the project to re-use the existing code snippets as much as possible, you may need to use
  functions like `list_files`, `read_file` and `write_file`.
  5. Writing the code into the file when creating new files, do not create empty files.
  6. If you are required to code base on the specific directory, you can use function `code_rag` to search the relatd codes in the specific directory, and remember you could only search one thing (like a function name, a class name, a variable name, etc.) in the codebase at a time.
  7. Before you write code into the existing files, you should first read the file content using function `read_file` and reserve the original content as much as possible.
  8. Decide whether the task requires execution and debugging before moving to the next or not.
  9. Generate the commands to run and test the current task, and the dependencies list for this task.
  10. You only write Python scripts, don't write Jupiter notebooks which require interactive execution.
  11. Note that every path you read, write, or search should be the absolute path (starting with '/').

  Your task is using existing project to create agents to complete the user request. 
  If the existing tools or agents are not enough for your task, you should develop new tools or agents. 
  Follow the following routine: 
  1. If there is enough pre-built tools and agents, create a python script in the `/{working_dir}/metachain` folder to run the agent to complete the user request.
  2. If you need to develop new tools, create a new tool in the `/{working_dir}/metachain/metachain/tools` folder.
  3. If you need to develop new agents, create a new agent in the `/{working_dir}/metachain/metachain/agents` folder.
  4. Create a python script in the `/{working_dir}/metachain` folder to run the new agent to complete the user request.

  Note that if you need OPENAI_API_KEY, my key is: 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
  """
      how_to_guides = context_variables.get("how_to_guides", None)
      if how_to_guides:
          ret_instructions += \
  f"""
  If you want to develop new tools or agents, you should follow the following guides:
  {how_to_guides}
  """
      return ret_instructions
    return Agent(
    name="Programming Agent",
    model=model,
    instructions=instructions,
    functions=[gen_code_tree_structure, execute_command, read_file, create_file, write_file, list_files, create_directory, run_python, code_rag, get_api_plugin_tools_doc],
    # examples=examples,
    tool_choice = "auto", 
    parallel_tool_calls = False
    )