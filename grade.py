import json
import os
import glob

# 配置你的日志目录
LOG_DIR = "new_logs"

def main():
    # 1. 查找所有 json 文件
    list_of_files = glob.glob(os.path.join(LOG_DIR, "*.json"))
    if not list_of_files:
        print(f"Error: No .json log files found in {LOG_DIR}")
        return

    # 按修改时间排序（最新的排在前面）
    list_of_files.sort(key=os.path.getmtime, reverse=True)

    print(f"Found {len(list_of_files)} log files. Starting analysis...")
    print("=" * 50)

    # 全局统计变量
    grand_total_correct = 0
    grand_total_tasks = 0

    best_strategy = ("None", 0.0)

    for filepath in list_of_files:
        filename = os.path.basename(filepath)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not data:
                print(f"[Skipping] {filename} (Empty file)")
                continue

            # --- 单个文件统计 ---
            correct_count = sum(1 for task in data if task.get("is_correct") is True)
            total_count = len(data)
            
            # 累加到全局
            grand_total_correct += correct_count
            grand_total_tasks += total_count

            # 计算正确率
            accuracy = correct_count / total_count if total_count > 0 else 0.0
            if accuracy > best_strategy[1]:
                best_strategy = (filename, accuracy)

            # --- 输出单文件报告 ---
            print(f"File: {filename}")
            print(f"  Result:   {correct_count}/{total_count}")
            print(f"  Accuracy: {accuracy:.2%}")

            print("-" * 50)

        except json.JSONDecodeError:
            print(f"[Error] {filename}: JSON format corrupted")
            print("-" * 50)
        except Exception as e:
            print(f"[Error] {filename}: {e}")
            print("-" * 50)
    
    print("=" * 50)
    print("Best Strategy:")
    print(f"File: {best_strategy[0]}")
    print(f"Accuracy: {best_strategy[1]:.2%}")

if __name__ == "__main__":
    main()