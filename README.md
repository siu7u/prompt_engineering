# PRML Final Project

## 1. project structure

```
PROMPT_ENGINEERING/
├── new_logs/                   # 存放运行日志
├── prompts/                    # 存放各策略的提示词文本
│   ├── {strategy_name}.txt     # 如: PAL.txt, cot.txt...
│   └── ...                     # 其他策略提示词文件
├── vis/                        # 可视化结果输出目录
│   ├── {strategy_name}/        # 对应策略的可视化文件夹
│   │   ├── line_0              # 任务 0 结果图的文件夹
│   │   ├── ...                 
│   │   └── line_29        
│   └── ...                     # 其他策略文件夹
├── grade.py                    # 评分脚本
├── README.md                   # 项目说明文档
├── template.py                 # 提示词模板构建脚本
├── test_prompt.py              # 主测试脚本
├── val.jsonl                   # 验证集数据
├── val_hard.jsonl              # 困难模式验证集
├── visualization.py            # 可视化脚本
└── requirements.txt
```

## 2.usage

Get the grades on different strategies.

```
python grade.py
```

Re-run the project

1. create an .env containing your api key:
```
DS_API_KEY = 'sk-xxxxx'
```

2. execute the following command

```
python test_prompt.py
```