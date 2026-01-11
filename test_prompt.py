import time
import os
import json
import re
from datetime import datetime
from openai import OpenAI

from dotenv import load_dotenv
from template import construct_prompt, parse_output
from visualization import save_task_visualization

STRATEGIES = ["empty",  #0
              "roleplay",
              "cot",
              'cot2',
              "hullucination_testing",
              "hullucination_testing2", #5
              "PAL",
              "PAL2",
              "PAL3",
              "PAL4", # 666，到达60%
              "fewshots", #10
              "self_identity",  #11
              "ReAct"
              ]

load_dotenv()
key = os.getenv("DS_API_KEY")
API_KEY = key
BASE_URL = "https://api.deepseek.com"
MODEL_NAME = "deepseek-chat"

DATA_PATH = "val.jsonl"
PROMPT_DIR = "prompts"
LOG_DIR = "new_logs"
VIS_DIR = "vis"
RETEST = False # 是否重复运行已完成的任务

STRATEGY_NAME = STRATEGIES[12]

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

def load_jsonl(path):
    data = []
    if not os.path.exists(path):
        print(f"Error: Data file not found at {path}")
        return []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def load_strategy_content(strategy_name):
    path = os.path.join(PROMPT_DIR, f"{strategy_name}.txt")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Strategy file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def save_compact_json(data, filepath):
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    def compact_elements(match):
        content = match.group(1)
        return f"[{content.replace(chr(10), '').replace(' ', '').replace(',', ', ')}]"
    pattern = r'\[\s*([\d,\s]+?)\s*\]'
    compact_json_str = re.sub(pattern, compact_elements, json_str)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(compact_json_str)

class LogManager:
    def __init__(self, log_dir, strategy_name, repeat):
        self.log_dir = log_dir
        self.repeat = RETEST
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        time = datetime.now().strftime("%Y%m%d_%H%M%S")
        if repeat:
            self.filename = f"results_log_{strategy_name}_repeat_{time}.json"
        else:
            self.filename = f"results_log_{strategy_name}.json"
        self.filepath = os.path.join(log_dir, self.filename)
        
        print(f"[Logging] target: {self.filepath}")

    def load_finished_tasks(self):
        """
        读取日志文件，返回已经完成的 task_id 集合。
        用于断点续传。
        """
        finished_ids = set()
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        history = json.loads(content)
                        for item in history:
                            if item.get("task_id"):
                                finished_ids.add(item["task_id"])
                print(f"[Resume] Found {len(finished_ids)} finished tasks in log.")
            except Exception as e:
                print(f"[Resume Warning] Failed to parse log file: {e}")
        return finished_ids

    def save_entry(self, entry):
        current_data = []
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        current_data = json.loads(content)
            except:
                pass # 文件损坏或为空，覆盖重写
        
        current_data.append(entry)
        save_compact_json(current_data, self.filepath)

def evaluate_single_task(task, model_name, system_prompt_content, max_retries=5):
    cur_retry = 0
    interval = 1 # 初始重试间隔设短一点
    task_id = task.get("task_id", "unknown")

    while cur_retry <= max_retries:
        try:
            # 1. 构造 Prompt
            messages = construct_prompt(task, system_prompt_content)
            
            # 2. 调用 API
            completion = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=1.0,
                max_tokens=8192
            )
            reply_text = completion.choices[0].message.content
            
            # 3. 解析输出
            pred_grid = parse_output(reply_text)
            
            if not pred_grid or not isinstance(pred_grid, list) or (len(pred_grid) > 0 and not isinstance(pred_grid[0], list)):
                raise ValueError("Invalid Grid Format: Output parsing failed or grid structure incorrect.")
            # 4. 获取 GT 并判定
            gt_grid = task.get('test', [{}])[0].get('output', [])
            
            is_correct = False
            if gt_grid:
                is_correct = (pred_grid == gt_grid)
            
            return {
                "task_id": task_id,
                "status": "Success",
                "is_correct": is_correct,
                "ground_truth": gt_grid,
                "predicted_output": pred_grid,
                "full_reply": reply_text,
                "retries_used": cur_retry
            }

        except Exception as e:
            cur_retry += 1
            print(f"  [Retry {cur_retry}/{max_retries}] Task {task_id} Error: {str(e)[:100]}...") # 只打印前100字符避免刷屏
            
            if cur_retry > max_retries:
                print(f"  [Fail] Task {task_id} failed after {max_retries} retries.")
                return {
                    "task_id": task_id,
                    "status": "Failed",
                    "error": str(e),
                    "is_correct": False,
                    "full_reply": locals().get('reply_text', 'No Response') # 尝试保留最后一次回复用于debug
                }
            
            # 指数退避策略
            time.sleep(interval)
            interval = min(interval * 2, 30) # 最大等待30秒

def main():
    # 1. 加载策略
    try:
        print(f"[Strategy] Loading: [{STRATEGY_NAME}]...")
        system_prompt_content = load_strategy_content(STRATEGY_NAME)
    except Exception as e:
        print(e)
        return

    # 2. 初始化日志管理器
    logger = LogManager(LOG_DIR, STRATEGY_NAME, RETEST)
    
    # 3. 【核心修改】读取已完成的任务ID，实现断点续传
    finished_task_ids = logger.load_finished_tasks()
    
    # 4. 加载数据
    tasks = load_jsonl(DATA_PATH)
    total_tasks = len(tasks)
    
    
    print(f"[Start] Evaluation: {total_tasks} tasks found.")
    print(f"[Resume] Skipping {len(finished_task_ids)} tasks already done.")
    print("="*60)

    session_correct = 0
    session_run_count = 0
    
    for idx, task in enumerate(tasks):
        task_id = task.get("task_id")
        if not task_id:
             task_id = f"line_{idx}" 
             task["task_id"] = task_id

        # 断点续传
        if task_id in finished_task_ids:
            continue
        
        print(f"[{idx+1}/{total_tasks}] Task {task_id} ... ", end="", flush=True)

        # 执行评测
        result_entry = evaluate_single_task(task, MODEL_NAME, system_prompt_content)
        
        # 结果符号
        if result_entry["status"] == "Success":
            if result_entry["is_correct"]:
                status_symbol = "[Correct]"
                session_correct += 1
            else:
                status_symbol = "[Wrong]"
        else:
            status_symbol = "[Failed]"
            
        print(status_symbol)
        session_run_count += 1

        # 可视化 (即便失败也尝试可视化，可能能看到部分结果)
        try:
            save_task_visualization(task_id, task, STRATEGY_NAME, result_entry, VIS_DIR)
        except Exception as e:
            # print(f"  [Vis Error]: {e}")
            pass

        # 实时存盘
        logger.save_entry(result_entry)
        
    print("="*60)
    if session_run_count > 0:
        print(f"Session Accuracy (Current Run): {session_correct}/{session_run_count} ({(session_correct/session_run_count):.2%})")
    else:
        print("No new tasks to run.")
        
    print(f"Logs updated: {logger.filepath}")
    print(f"Visualizations: {VIS_DIR}/")

if __name__ == "__main__":
    main()