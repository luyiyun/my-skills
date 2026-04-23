# Repository Bootstrap Workflow

这个参考文件描述如何初始化或整理一个 Python + uv 的方法学研究项目仓库。

## 1. 检查顺序

开始前先检查：

- 当前仓库根目录。
- `pyproject.toml`、`uv.lock`、`.python-version` 是否存在。
- `src/` 下已有包和模块。
- 根目录是否已有 `main.py`、`AGENTS.md`、`tests/`。

若是现有仓库：

- 沿用现有包名和入口，除非已有命名明显错误。
- 做最小增量修改，不顺手大改无关结构。

## 2. 默认目录骨架

初始化时优先使用下面这类布局：

```text
repo/
├── AGENTS.md
├── main.py
├── pyproject.toml
├── src/
│   ├── <pkg>/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── data.py
│   │   └── estimator.py
│   ├── <pkg>_simulate/
│   │   └── __init__.py
│   └── <pkg>_case/
│       └── __init__.py
└── tests/
    ├── test_imports.py
    └── test_main.py
```

说明：

- `src/<pkg>` 是主包，放可复用方法学实现。
- `src/<pkg>_simulate` 与 `src/<pkg>_case` 是围绕主包展开的实验层。
- 这两个实验层可以组织得务实一些，不必为了“像库”而过度抽象。

## 3. uv 初始化和依赖策略

默认初始化命令：

```bash
uv init --package
```

如果你是在另一个 `uv` workspace 或 monorepo 下面创建嵌套项目，而你并不想把它自动注册到父 workspace，优先使用：

```bash
uv init --package --no-workspace
```

通用开发依赖优先包含：

```bash
uv add --dev ruff pyright pytest
```

通用 ML 项目默认运行时依赖：

```bash
uv add pydantic
```

PyTorch DL 项目常见运行时依赖：

```bash
uv add pydantic torch torchmetrics
```

只有在上下文明确要求时，再补 `numpy`、`pandas`、`scikit-learn` 等其他依赖。

## 4. `pyproject.toml` 建议

优先把 `ruff` 和 `pyright` 配置写进 `pyproject.toml`。下面是一个可复用的最小示例：

```toml
[tool.ruff]
line-length = 100
src = ["src", "tests"]
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.pyright]
include = ["src", "tests", "main.py"]
typeCheckingMode = "standard"
```

要点：

- `I` 规则保证 import 排序。
- `typeCheckingMode = "standard"` 作为默认严格度。
- 若项目实际 Python 版本不同，再同步调整 `target-version`。

## 5. `main.py` 设计原则

`main.py` 是运行入口，但子命令必须按项目上下文动态生成。

推荐顺序：

1. 先判断项目有哪些实际运行流。
2. 只生成最少必要子命令。
3. 后续需求出现时再扩展 CLI。

默认示例：

- 通用 ML 项目：通常先有 `train`。
- 有模拟实验：再加 `simulate`。
- 有案例验证：再加 `case`。

不要为了“模板统一”提前塞很多不会用到的子命令。

如果 `uv init --package` 生成了默认的 `[project.scripts]`，记得把它和最终入口设计对齐：

- 如果你保留包级入口，就确保 `<pkg>:main` 真能运行。
- 如果真正的主入口已经转到根目录 `main.py`，就更新或移除默认脚本配置。

不要留下一个表面存在、实际失效的 console script。

## 6. smoke tests 基线

初始化阶段就创建最小测试，至少覆盖：

- 主包可以正常 import。
- 若存在 CLI，`main.py --help` 或对应解析逻辑可正常运行。

当新增大功能时：

- 补对应该功能的单元测试。
- 不要只停留在 smoke test。

## 7. 主包与实验包的导入约定

在 `src/<pkg>` 中：

- 优先相对导入，例如 `from .model import ModelClass`。

在 `src/<pkg>_simulate` 与 `src/<pkg>_case` 中：

- 把自己当成主包使用者。
- 优先绝对导入，例如 `from <pkg>.estimator import EstimatorClass`。

这样更贴近真实使用方式，也能减少重复实现。
