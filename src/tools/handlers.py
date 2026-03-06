import subprocess
import json

def run_terminal_command(command: str, args: list):
    with open('tools/whitelist.json', 'r') as f:
        whitelist = json.load(f)

    if command not in whitelist['allowed_commands']:
        return f"Exception: Command '{command}' not allowed!"

    result = subprocess.run([command] + args, capture_output=True, text=True)
    return result.stdout

def run_python_skill(skill_name: str, params: list):
    with open('tools/whitelist.json', 'r') as f:
        whitelist = json.load(f)

    if skill_name not in whitelist['allowed_scripts']:
        return f"Exception: Skill '{skill_name}' not found!"

    result = subprocess.run(["python3", f"skills/{skill_name}"] + params, capture_output=True, text=True)
    return result.stdout