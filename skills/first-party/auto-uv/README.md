# Auto-UV Skill for Claude Code

让 Claude 在处理任何 Python 任务时自动使用 UV 包管理器，告别 pip 和手动虚拟环境管理。

## 简介

Auto-UV 是一个 Claude Code Skill，它会自动：
- 检测当前目录是否为 UV 项目
- 自动初始化 UV 项目（如需要）
- 使用 `uv run` 执行所有 Python 脚本
- 使用 `uv add` 安装项目依赖
- 确保其他 Skill 调用 Python 时也使用 UV

## 为什么选择 UV？

[UV](https://github.com/astral-sh/uv) 是一个用 Rust 编写的极速 Python 包管理器：
- ⚡ **10-100倍更快** 的包安装速度
- 🔒 **自动虚拟环境管理**，无需手动激活
- 📦 **统一的工具链**：替代 pip、pip-tools、pipx、poetry、virtualenv
- 🚀 **零配置**，开箱即用

## 核心原则

> **只要涉及 Python，就使用 UV。**

## 安装

将本 skill 复制到你的 Claude Code skills 目录：

```bash
# Claude Code skills 目录位置
# Windows: %USERPROFILE%\.claude\skills\
# Linux/Mac: ~/.claude/skills/

cp -r auto-uv ~/.claude/skills/
```

## 使用方式

安装后，Claude 会在处理 Python 任务时自动使用 UV。

### 示例场景

#### 1. 运行 Python 脚本
```bash
# 传统方式
python script.py

# Auto-UV 方式
uv run script.py
```

#### 2. 安装依赖
```bash
# 长期项目开发
uv add pandas numpy matplotlib

# 一次性任务
uv run --with pandas script.py

# pip 兼容模式
uv pip install pandas
```

#### 3. 创建新项目
```bash
# 自动执行
uv init
uv add requests fastapi
uv run main.py
```

## Skill 功能

### 自动检测与初始化
- 检查 `pyproject.toml`、`uv.lock` 等 UV 项目标识
- 自动运行 `uv init` 初始化新项目
- 自动迁移 `requirements.txt` 中的依赖

### 三种依赖安装方式

| 场景 | 命令 | 特点 |
|------|------|------|
| 长期项目 | `uv add package` | 写入 pyproject.toml，适合版本控制 |
| 一次性运行 | `uv run --with package script.py` | 临时环境，不修改项目文件 |
| pip 兼容 | `uv pip install package` | 与 pip 语法完全一致 |

### 其他 Skill 兼容

当使用 seaborn、scikit-learn、exploratory-data-analysis 等其他 skill 时，Auto-UV 会确保：
- 这些 skill 的 Python 脚本通过 UV 执行
- 依赖自动安装，无需手动 pip install

## 快速参考

| 传统方式 | UV 方式 | 使用场景 |
|---------|---------|---------|
| `python script.py` | `uv run script.py` | 运行脚本 |
| `pip install package` | `uv add package` | 项目依赖 |
| `pip install package` | `uv run --with package script.py` | 临时依赖 |
| `python -m pytest` | `uv run pytest` | 运行工具 |
| `python -m venv .venv` | `uv venv` | 创建虚拟环境 |

## 目录结构

```
auto-uv/
├── SKILL.md          # Skill 核心逻辑（必需）
├── README.md         # 本文件
└── evals/            # 测试用例
    └── evals.json
```

## 测试

本 skill 包含测试用例，用于验证：
- 运行 Python 脚本时使用 UV
- 安装依赖时使用 UV
- 其他 skill 调用 Python 时使用 UV

## 故障排除

### UV 未安装
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

## 相关链接

- [UV 官方文档](https://docs.astral.sh/uv/)
- [UV GitHub](https://github.com/astral-sh/uv)
- [Claude Code Skills 文档](https://docs.anthropic.com/en/docs/claude-code/skills)

## 许可证

MIT License
