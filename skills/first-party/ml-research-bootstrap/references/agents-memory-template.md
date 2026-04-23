# `AGENTS.md` Template For ML Research Projects

在项目根目录创建或更新 `AGENTS.md` 时，优先覆盖下面这些栏目。若仓库里已经有 `AGENTS.md`，默认把这些栏目增量合并进去。

```md
# Project Guide

## Purpose

用 2-4 句话说明：

- 项目研究目标是什么。
- 当前项目主要解决哪类方法学问题。
- 当前阶段的范围与非目标是什么。

## Layout

- `src/<pkg>/`: 主包，放模型、方法、训练与复用逻辑。
- `src/<pkg>_simulate/`: 模拟实验代码，把自己当成主包使用者。
- `src/<pkg>_case/`: 实例验证代码，把自己当成主包使用者。
- `main.py`: 命令行入口，通过 `uv run main.py ...` 运行。
- `tests/`: 单元测试与 smoke tests。
- `AGENTS.md`: 项目记忆 + 长期工作规范。

## Workflow

1. 先检查当前结构与已有约定，再决定如何改动。
2. 默认用 `uv` 管理项目与依赖。
3. 优先把复用逻辑写进 `src/<pkg>`，避免在 `simulate`/`case` 中重复造轮子。
4. 新增大功能后补对应单元测试。
5. 完成功能后运行格式化、lint、类型检查和测试。
6. 若架构或工作规范发生变化，同步更新本文件。

## Coding Rules

- Python 是主要开发语言，默认使用 `uv init --package` 初始化。
- 所有新增代码必须带类型注解。
- `pyright` 使用 `standard` 模式。
- import 尽量放在文件顶部。
- `src/<pkg>` 内优先相对导入。
- `src/<pkg>_simulate` 与 `src/<pkg>_case` 内优先绝对导入主包。
- 尽量不要写 `try/except`，除非确有恢复、转换或增强诊断的必要。
- 每次完成大的功能更新，都必须新增或更新对应单元测试。

## Verification

完成代码修改后按顺序运行：

1. `uv run ruff format`
2. `uv run ruff check --fix`
3. `uv run pyright`
4. `uv run pytest`

如果某一步失败，先修复再继续。

## Current Decisions

记录当前有效的架构决策，例如：

- 主入口有哪些 CLI 子命令，为什么这样设计。
- 当前主模型/数据/训练接口如何分层。
- `simulate` 与 `case` 当前承担哪些任务。
- 是否启用了 PyTorch DL estimator/data/model/trainer 结构。

## Open Notes

记录会影响后续工作的短期记忆，例如：

- 当前正在开发的大功能。
- 待补充的测试点。
- 近期做出的非显然权衡。
```

## 使用建议

- 把这份模板当成基线，而不是强制逐字复制。
- 若项目已有成熟记忆结构，优先合并而不是重写。
- 只保留对后续协作真正有帮助的信息，避免把 `AGENTS.md` 写成流水账。
