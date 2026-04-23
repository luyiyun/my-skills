---
name: ml-research-bootstrap
description: 当用户要初始化、重构或规范化一个机器学习或深度学习方法学研究项目库时使用。适用于 Python + uv 项目搭建、默认执行 `uv init --package`、创建 `src/<包名>` / `src/<包名>_simulate` / `src/<包名>_case` 结构、补根目录 `main.py` 命令行入口、补 `AGENTS.md` 长期工作规范、补 `tests/`，以及把现有仓库整理成可复用的 ML/DL 研究模板。遇到 PyTorch 深度学习项目时，还应按 estimator/data/model/trainer/config/metrics 的方式组织主包代码。
---

# ML Research Bootstrap

帮助用户初始化或持续扩展 Python + uv 的机器学习/深度学习方法学研究项目库，让项目从一开始就具备可复用的包结构、命令行入口、测试和项目级工作规范。

## 默认工作原则

把下面四条作为默认行为，而不是可选建议：

- 先澄清再动手：先检查仓库现状、目录结构、`pyproject.toml`、`main.py`、`AGENTS.md` 和 `tests/`，不要凭空假设。
- 简单优先：只实现当前需求真正需要的项目骨架，不预埋用户没要的复杂抽象。
- 外科手术式改动：若是在已有仓库上工作，只增量修改必要内容；已有 `AGENTS.md` 时默认合并补充规范，而不是整篇重写。
- 用可验证目标驱动实现：完成代码后固定运行格式化、lint、类型检查；有测试就跑测试，大功能更新必须补单元测试。

## 何时使用

在下面这些场景里优先使用这个 skill：

- 用户要新建一个机器学习或深度学习方法学研究项目仓库。
- 用户要把现有研究代码改成 `uv` 管理的包式项目。
- 用户要补 `src/<pkg>`、`src/<pkg>_simulate`、`src/<pkg>_case` 这种三层结构。
- 用户要给研究项目补 `main.py` CLI 入口、`tests/`、`AGENTS.md`。
- 用户要给 PyTorch 方法学项目建立 estimator/data/model/trainer/config/metrics 架构。
- 用户要在现有仓库上继续做结构化扩展，并沿用统一的 Python/uv/ruff/pyright/test 规范。

## 工作流程

### 1. 先检查，再推断

优先检查：

- 当前目录和仓库名。
- 是否已有 `pyproject.toml`、`uv.lock`、`main.py`、`AGENTS.md`、`tests/`。
- `src/` 下已有包名、入口模块和实验目录。

从上下文尽量推断：

- 包名：优先用现有 `project.name`、`src/` 目录名或仓库名归一化后的结果。
- 模式：
  - 若用户明确提到 PyTorch、神经网络、`nn.Module`、trainer、dataset、checkpoint、torchmetrics，则按 PyTorch DL 模式处理。
  - 否则默认按通用 ML 模式处理。

只在以下信息无法安全推断时再问用户：

- 目标路径。
- 包名。
- 当前项目属于通用 ML 还是 PyTorch DL。

### 2. 默认项目骨架

除非上下文明确要求别的布局，否则默认目标是：

- 使用 `uv init --package` 初始化项目。
- 若项目目录位于另一个 `uv` workspace 或 monorepo 之内，先判断是否真的要把它注册成 workspace member；若不是，就优先使用 `uv init --package --no-workspace`。
- 把主代码放到 `src/<pkg>`。
- 创建 `src/<pkg>_simulate` 存放模拟实验代码。
- 创建 `src/<pkg>_case` 存放实例验证代码。
- 在根目录创建 `main.py` 作为命令行入口。
- 在根目录创建或更新 `AGENTS.md`，把项目记忆和长期工作规范都写进去。
- 创建 `tests/`，并加入最小 smoke tests。

主包与实验包的职责要分清：

- `src/<pkg>`：方法、模型、训练与复用逻辑。
- `src/<pkg>_simulate`：把自己当成主包的使用者来写模拟实验代码。
- `src/<pkg>_case`：把自己当成主包的使用者来写案例验证代码。

### 3. `main.py` 要动态设计

不要把 `train`、`simulate`、`case` 写死成统一模板。

按项目上下文生成最少必要的子命令：

- 通用 ML 新项目通常先给一个最小可运行子命令，例如 `train`。
- 只有项目明确存在模拟实验、案例验证或其他运行流时，才补 `simulate`、`case` 或其他子命令。
- CLI 统一使用标准库 `argparse`。
- 运行方式统一保持为 `uv run main.py ...`。
- 若 `uv init --package` 自动生成了 `[project.scripts]` 指向 `<pkg>:main`，要同步处理它：要么保留一个有效的包级 `main()` 包装入口，要么更新/移除这条脚本配置；不要留下失效的 console script。

### 4. 两种模式的实现边界

#### 通用 ML 模式

保持骨架轻量。只放当前任务需要的最小模块，例如：

- `__init__.py`
- `config.py`
- `data.py`
- `estimator.py`

不要因为“以后可能会用到”就强行生成完整深度学习训练框架。

#### PyTorch DL 模式

启用完整的 estimator/data/model/trainer/config/metrics 结构。具体约定见 [references/pytorch-estimator-architecture.md](references/pytorch-estimator-architecture.md)。

核心要求：

- 主入口是 sklearn 风格的 estimator 对象，不要求继承 sklearn 基类。
- estimator 需要实现 `fit`、`predict`，并按需实现 `predict_proba`、`transform`。
- estimator 还需要实现 `save`、`load`（类方法）、`test`。
- `data`、`model`、`trainer`、`estimator` 都使用基于 Pydantic 的 config 类。
- 优先使用 `torchmetrics`；缺失时再自定义兼容类。

## 代码规范

- 所有新增 Python 代码都加类型注解。
- `pyright` 使用 `standard` 模式。
- 项目内 import 尽量放在文件顶部。
- `src/<pkg>` 内优先使用相对导入复用自研模块。
- `src/<pkg>_simulate` 与 `src/<pkg>_case` 内优先使用 `import <pkg>` 或 `from <pkg> import ...`。
- 尽量不要写 `try/except`，让错误自然暴露；只有在上下文明确需要恢复、转换或补充诊断信息时才添加异常处理。
- 初始化阶段也要创建最小 smoke tests，至少覆盖主包导入和基础 CLI。
- 每次完成较大的功能更新，都要补对应单元测试。

## `AGENTS.md` 维护要求

`AGENTS.md` 不只是项目记忆文件，也要承载长期工作规范。

创建或更新时至少覆盖：

- 项目目标与当前范围。
- 目录地图与三个包的职责边界。
- 常用命令：`uv run main.py ...`、格式化、lint、类型检查、测试。
- Python/uv/ruff/pyright/type hints/import/少 `try/except` 等规范。
- 大功能更新后必须补单元测试、跑检查，并同步更新 `AGENTS.md`。

优先参考 [references/agents-memory-template.md](references/agents-memory-template.md)。

## 完成后的验证顺序

完成代码修改后，按下面顺序验证：

1. `uv run ruff format`
2. `uv run ruff check --fix`
3. `uv run pyright`
4. 若项目已有测试或你本次新增了测试，再运行 `uv run pytest`

如果验证失败，先修复问题，再结束任务。

## 参考资料

- 总体初始化流程与 `pyproject.toml` 建议： [references/repo-bootstrap-workflow.md](references/repo-bootstrap-workflow.md)
- PyTorch 深度学习主包结构： [references/pytorch-estimator-architecture.md](references/pytorch-estimator-architecture.md)
- `AGENTS.md` 模板与长期规范栏目： [references/agents-memory-template.md](references/agents-memory-template.md)
