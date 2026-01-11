import os
import matplotlib.pyplot as plt
from matplotlib import colors
import numpy as np

# ARC 标准 10 色定义
ARC_COLORS = [
    "#000000", # 0: Black
    "#0074D9", # 1: Blue
    "#FF4136", # 2: Red
    "#2ECC40", # 3: Green
    "#FFDC00", # 4: Yellow
    "#AAAAAA", # 5: Grey
    "#F012BE", # 6: Fuchsia
    "#FF851B", # 7: Orange
    "#7FDBFF", # 8: Teal
    "#870C25", # 9: Maroon
]

def plot_grid(grid, ax, title=""):
    """绘制单个网格"""
    if not grid or not isinstance(grid, list):
        ax.text(0.5, 0.5, "Invalid Grid", ha='center', va='center')
        ax.axis('off')
        return

    height = len(grid)
    width = len(grid[0]) if height > 0 else 0

    cmap = colors.ListedColormap(ARC_COLORS)
    norm = colors.Normalize(vmin=0, vmax=9)

    ax.imshow(grid, cmap=cmap, norm=norm)
    
    # 绘制网格线
    ax.set_xticks(np.arange(-0.5, width, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, height, 1), minor=True)
    ax.grid(which="minor", color="w", linestyle='-', linewidth=1)
    ax.tick_params(which="minor", bottom=False, left=False)
    
    # 移除坐标轴刻度
    ax.set_xticks([])
    ax.set_yticks([])
    
    if title:
        ax.set_title(title, fontsize=10, pad=5)

def save_task_visualization(task_id, task_data, strategy ,result_entry, output_dir="vis"):
    """
    生成并保存任务的可视化图像
    """
    save_path = os.path.join(output_dir, strategy, str(task_id))
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    # 1. 绘制训练示例
    train_exs = task_data.get('train', [])
    for idx, ex in enumerate(train_exs):
        fig, axs = plt.subplots(1, 2, figsize=(6, 3))
        plot_grid(ex['input'], axs[0], f"Train {idx+1} Input")
        plot_grid(ex['output'], axs[1], f"Train {idx+1} Output")
        plt.tight_layout()
        plt.savefig(os.path.join(save_path, f"train_{idx+1}.png"))
        plt.close(fig)

    # 2. 绘制测试及预测结果对比
    # 如果预测成功，画 Input | Ground Truth | Prediction
    # 如果失败或没有GT，根据情况画
    
    test_input = task_data['test'][0]['input']
    gt_output = task_data['test'][0].get('output', None) # 有可能有些集没有GT
    pred_output = result_entry.get('predicted_output', None)
    is_correct = result_entry.get('is_correct', False)
    
    cols = 2
    if gt_output is not None: cols += 1
    if pred_output is not None: cols = 3 # 强制展示对比

    fig, axs = plt.subplots(1, cols, figsize=(3 * cols, 3))
    
    # 处理 axs 下标，如果 cols=1 它是对象，cols>1 它是数组
    if cols == 1: axs = [axs]
    
    plot_grid(test_input, axs[0], "Test Input")
    
    current_idx = 1
    if gt_output is not None:
        plot_grid(gt_output, axs[current_idx], "Ground Truth")
        current_idx += 1
        
    if pred_output is not None:
        status = "CORRECT" if is_correct else "WRONG"
        plot_grid(pred_output, axs[current_idx], f"Prediction ({status})")

    plt.tight_layout()
    plt.savefig(os.path.join(save_path, f"test_result_{'CORRECT' if is_correct else 'FAIL'}.png"))
    plt.close(fig)