---
name: auto-uv
description: 当用户使用Python相关功能时，自动使用UV进行项目管理。包括：自动检测UV项目、初始化UV环境、使用uv run执行Python脚本、使用uv add/uv pip install安装依赖。适用于所有Python代码执行、包安装、项目设置场景。无论是数据分析、脚本运行、Web开发还是机器学习任务，只要涉及Python，就优先使用UV。关键词：python, pip install, 运行python, python脚本, requirements.txt, 虚拟环境, venv
---

# Auto-UV - 自动UV项目管理

## 核心原则

**只要涉及Python，就使用UV。**

Claude在处理任何Python相关任务时，应该默认使用UV作为包管理器和项目工具，而不是传统的pip或裸Python执行。

## 自动检测与初始化

### 步骤1：检测UV项目

在执行任何Python操作之前，检查当前目录是否为UV项目：

```bash
# 检查是否存在UV项目标识文件
ls pyproject.toml uv.lock .python-version 2>/dev/null
```

### 步骤2：自动初始化（如需要）

如果当前目录没有UV项目标识，**自动执行初始化**：

```bash
# 初始化UV项目
uv init
```

**注意：** 如果目录已存在 `requirements.txt`，在初始化后应将其依赖导入：

```bash
# 将requirements.txt中的依赖添加到UV项目
if [ -f "requirements.txt" ]; then
    uv add $(cat requirements.txt | grep -v "^#" | grep -v "^$")
fi
```

## 执行Python代码

### 运行Python脚本

**不要这样做：**
```bash
python script.py
python3 script.py
```

**应该这样做：**
```bash
uv run script.py
```

### 交互式Python

**不要这样做：**
```bash
python
ipython
```

**应该这样做：**
```bash
uv run python
# 或使用ipython（如已安装）
uv run ipython
```

### 模块执行

**不要这样做：**
```bash
python -m pytest
python -m flask
```

**应该这样做：**
```bash
uv run pytest
uv run flask
```

## 安装依赖

### 方式选择决策树

在选择安装方式前，**先读取上下文线索**，而不是随机猜测：

```
需要安装Python包？
│
├─ 步骤1：读取上下文信号
│  ├─ 当前目录有 pyproject.toml？→ 这是已有项目 → 优先用 uv add
│  ├─ 用户正在开发某个功能/项目？→ 长期项目 → 用 uv add
│  ├─ 用户说"帮我分析这个文件"/"快速看看"/"试一下"？→ 一次性任务 → 用 uv run --with
│  └─ 上下文不明确？→ 继续步骤2
│
├─ 步骤2：根据任务性质判断
│  ├─ 用户在开发/构建某个产品或服务 → 长期项目 → 用 uv add
│  ├─ 用户只是想运行一个脚本/分析一个数据集 → 一次性 → 用 uv run --with
│  └─ 真的无法判断 → 步骤3
│
├─ 步骤3：上下文完全不明确时，询问用户
│  └─ "这是用于长期项目开发，还是一次性任务？"
│     ├─ 长期项目 → uv add package（依赖写入 pyproject.toml）
│     └─ 一次性任务 → uv run --with package script.py（临时环境）
│
└─ 需要pip兼容行为（如迁移过渡期）？
   └─ YES → uv pip install package
```

**关键原则：当用户说"帮我安装 X"时，不要直接跳到一次性方式。先看看：**
- 有没有 pyproject.toml？→ 有的话用 `uv add`
- 整个会话上下文暗示是项目开发吗？→ 用 `uv add`
- 真的是随手一问，没有任何项目背景？→ 才用 `uv run --with` 或询问

### 方式1：项目依赖（推荐用于长期项目）

使用 `uv add` 将依赖添加到项目：

```bash
# 添加生产依赖（会更新pyproject.toml）
uv add requests pandas numpy

# 添加开发依赖
uv add --dev pytest black mypy

# 添加特定版本
uv add "requests>=2.28.0"

# 从requirements.txt导入
uv add -r requirements.txt
```

**适用场景：**
- 长期维护的项目
- 需要版本控制依赖
- 团队协作项目

### 方式2：一次性运行（推荐用于临时任务）

使用 `uv run --with` 临时安装并运行：

```bash
# 临时安装包并运行脚本（不修改项目文件）
uv run --with pandas python -c "import pandas; print('ok')"

# 同时安装多个包
uv run --with pandas --with numpy --with matplotlib script.py

# 运行单个Python文件
uv run --with requests script.py
```

**适用场景：**
- 一次性数据分析任务
- 快速测试某个包
- 不希望在项目中留下依赖记录

### 方式3：pip兼容模式

使用 `uv pip install`（与pip语法完全一致）：

```bash
# 使用uv pip install（与pip语法兼容）
uv pip install requests
uv pip install -r requirements.txt
```

**适用场景：**
- 从pip迁移的过渡期
- 需要与现有pip工作流兼容
- 不需要UV的项目管理功能

### 三种方式对比

| 场景 | 推荐命令 | 是否修改pyproject.toml | 依赖持久化 |
|------|---------|----------------------|-----------|
| 长期项目开发 | `uv add package` | ✅ 是 | ✅ 是 |
| 一次性/临时运行 | `uv run --with package script.py` | ❌ 否 | ❌ 否（临时环境） |
| pip兼容 | `uv pip install package` | ❌ 否 | ❌ 否（仅当前环境） |

## 其他 Skill 调用 Python 时的处理

当使用其他 Skill（如 seaborn、scikit-learn、exploratory-data-analysis 等）时，如果这些 Skill 需要执行 Python 代码或安装 Python 包，**也必须使用 UV**。

### 原则

**无论什么 skill，只要最终需要执行 Python，就应该通过 UV 来执行。**

### 典型场景

**场景1：使用 seaborn skill 创建图表**

```bash
# 错误：让 seaborn skill 直接使用 python
python create_chart.py

# 正确：使用 uv run 执行
uv run --with seaborn --with matplotlib create_chart.py
```

**场景2：使用 exploratory-data-analysis skill 分析数据**

```bash
# 错误：直接使用系统 Python
python analyze_data.py

# 正确：先确保 UV 项目初始化，然后使用 uv run
uv init  # 如果需要
uv add pandas numpy  # 如果需要
uv run analyze_data.py
```

**场景3：使用 scikit-learn skill 进行机器学习**

```bash
# 错误：使用 pip install 安装依赖
pip install scikit-learn

# 正确：使用 UV 管理依赖
uv add scikit-learn
uv run train_model.py
```

### 实现方式

当调用其他 skill 时：

1. **检查该 skill 是否需要执行 Python**
   - 如果需要创建/运行 Python 脚本 → 使用 UV
   - 如果需要安装 Python 包 → 使用 UV

2. **在执行前自动执行 UV 检测/初始化**
   ```bash
   # 检查并初始化 UV 项目
   if [ ! -f "pyproject.toml" ]; then
       uv init
   fi
   ```

3. **使用 uv run 执行所有 Python 脚本**
   - 对于一次性运行：`uv run --with package script.py`
   - 对于项目脚本：`uv run script.py`

### 示例：调用 seaborn skill 时使用 UV

```bash
# 1. 用户说：使用 seaborn 创建一个数据可视化图表

# 2. 自动检查 UV 项目状态
ls pyproject.toml || uv init

# 3. 安装 seaborn 依赖（如果需要）
uv add seaborn matplotlib pandas

# 4. 创建可视化脚本
# ... (创建脚本代码) ...

# 5. 使用 uv run 执行脚本
uv run visualization.py
```

### 注意事项

- **不要假设其他 skill 会处理依赖** - 即使 skill 文档提到 pip，也应该转换为 UV
- **保持环境一致性** - 一个会话中的所有 Python 操作应该使用同一个 UV 项目
- **优先使用项目方式** - 如果确定是长期项目，使用 `uv add`；如果只是临时任务，使用 `uv run --with`

## 虚拟环境管理

### 创建虚拟环境

**不要这样做：**
```bash
python -m venv .venv
virtualenv .venv
```

**应该这样做：**
```bash
# UV会自动管理虚拟环境，通常不需要手动创建
# 但如果需要显式创建：
uv venv
```

### 激活虚拟环境

UV的 `uv run` 命令会自动使用项目虚拟环境，**不需要手动激活**。

但如果需要手动激活（如在终端中）：

```bash
# Windows (Git Bash)
source .venv/Scripts/activate

# Windows (CMD)
.venv\Scripts\activate.bat

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Linux/Mac
source .venv/bin/activate
```

## Python版本管理

### 指定Python版本

```bash
# 查看可用Python版本
uv python list

# 安装特定版本
uv python install 3.12

# 为项目固定Python版本
uv python pin 3.12
```

### 使用特定Python版本运行

```bash
# 使用特定Python版本
uv run --python 3.11 script.py
```

## 常用场景示例

### 数据分析任务

```bash
# 假设用户说：帮我分析一下这个CSV文件

# 1. 检查/初始化UV项目
ls pyproject.toml || uv init

# 2. 添加数据分析依赖
uv add pandas matplotlib seaborn

# 3. 运行分析脚本
uv run analysis.py
```

### Web开发（FastAPI/Flask）

```bash
# 1. 检查/初始化UV项目
ls pyproject.toml || uv init

# 2. 添加Web框架依赖
uv add fastapi uvicorn
# 或
uv add flask

# 3. 运行开发服务器
uv run uvicorn main:app --reload
# 或
uv run flask run
```

### 机器学习项目

```bash
# 1. 检查/初始化UV项目
ls pyproject.toml || uv init

# 2. 添加ML依赖
uv add scikit-learn numpy pandas matplotlib

# 3. 运行训练脚本
uv run train.py
```

### 运行测试

```bash
# 添加测试框架
uv add --dev pytest

# 运行测试（使用uv run）
uv run pytest

# 带覆盖率报告
uv run pytest --cov=src tests/
```

### 代码格式化与检查

```bash
# 添加开发工具
uv add --dev black isort flake8 mypy

# 运行代码格式化
uv run black .
uv run isort .

# 运行类型检查
uv run mypy src/
```

## 处理现有项目

### 迁移pip项目

```bash
# 1. 初始化UV项目（如果还没有）
uv init

# 2. 从requirements.txt导入依赖
if [ -f "requirements.txt" ]; then
    uv add -r requirements.txt
fi

# 3. 从requirements-dev.txt导入开发依赖（如果存在）
if [ -f "requirements-dev.txt" ]; then
    uv add --dev -r requirements-dev.txt
fi

# 4. 删除旧的requirements文件（可选）
rm requirements.txt requirements-dev.txt 2>/dev/null
```

### 处理setup.py项目

```bash
# 1. 初始化UV项目
uv init

# 2. 提取setup.py中的依赖（手动或脚本方式）
# 然后使用uv add添加

# 3. 迁移完成后可以删除setup.py
```

## 故障排除

### UV命令不可用

如果系统没有安装UV：

```bash
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/Mac
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 依赖冲突

```bash
# 查看依赖树
uv pip tree

# 更新所有依赖
uv sync --upgrade
```

### 锁定文件问题

```bash
# 重新生成锁定文件
rm uv.lock
uv sync
```

## 最佳实践总结

1. **始终检查UV项目状态** - 在执行Python任务前，先检查pyproject.toml是否存在
2. **自动初始化** - 如果不是UV项目，自动运行 `uv init`
3. **使用uv run** - 执行任何Python代码都使用 `uv run script.py`
4. **使用uv add** - 安装项目依赖使用 `uv add package_name`
5. **提交锁定文件** - 提示用户提交 `uv.lock` 文件到版本控制

## 快速参考表

| 传统方式 | UV方式 | 使用场景 |
|---------|--------|---------|
| `python script.py` | `uv run script.py` | 运行脚本（依赖已安装） |
| `python script.py` (需要临时依赖) | `uv run --with package script.py` | 临时运行，自动安装依赖 |
| `pip install requests` | `uv add requests` | 长期项目添加依赖 |
| `pip install requests` | `uv pip install requests` | pip兼容模式 |
| `pip install -r requirements.txt` | `uv add -r requirements.txt` | 导入requirements |
| `python -m pytest` | `uv run pytest` | 运行工具 |
| `python -m venv .venv` | `uv venv` | 创建虚拟环境（通常不需要） |
| `source .venv/bin/activate` | `uv run` | 自动使用虚拟环境 |
