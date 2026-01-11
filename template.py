import json
import re
import ast

def construct_prompt(d, system_prompt_content):
    """
    构造提示词
    :param d: 单个任务数据
    :param system_prompt_content: 从 txt 读取的策略字符串
    """
    training_examples = d.get('train', [])
    test_example = d.get('test', [{}])[0]
    messages = []
    
    # 1. System Prompt (直接使用传入的内容)
    messages.append({"role": "system", "content": system_prompt_content})

    # 2. User Prompt (拼接训练数据)
    user_prompt = "Here are the training examples:\n\n"

    for idx, ex in enumerate(training_examples):
        user_prompt += f"--- Example {idx + 1} ---\n"
        user_prompt += "Input:\n"
        user_prompt += json.dumps(ex['input']) + "\n\n"
        user_prompt += "Output:\n"
        user_prompt += json.dumps(ex['output']) + "\n\n"

    user_prompt += "--- TEST TASK ---\n"
    user_prompt += "Use the rule found above to generate the Output for this Test Input:\n"
    user_prompt += json.dumps(test_example['input']) + "\n\n"
    user_prompt += "Please provide the Reasoning and the Final Output Grid."

    messages.append({"role": "user", "content": user_prompt})

    return messages

def parse_output(text):
    """
    解析大语言模型的输出文本
    """
    # 1. 预处理：尝试提取 markdown 代码块
    code_block_pattern = r"```(?:json|python)?\s*(.*?)```"
    code_blocks = re.findall(code_block_pattern, text, re.DOTALL)
    
    if code_blocks:
        target_text = code_blocks[-1]
    else:
        target_text = text

    target_text = target_text.strip()

    # 2. 物理定位法
    start_index = target_text.find('[[')
    end_index = target_text.rfind(']]')

    if start_index == -1 or end_index == -1:
        return [] 

    candidate_str = target_text[start_index : end_index + 2]

    # 3. 尝试解析
    try:
        grid = json.loads(candidate_str)
    except json.JSONDecodeError:
        try:
            grid = ast.literal_eval(candidate_str)
        except Exception:
            try:
                grid = ast.literal_eval(candidate_str + "]]")
            except:
                return []

    if not isinstance(grid, list):
        return []
    
    return grid