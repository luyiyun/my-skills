# PyTorch Estimator Architecture

当项目明确属于 PyTorch 深度学习方法学研究时，主包优先采用下面这套最小可用结构。

## 1. 推荐目录

```text
src/<pkg>/
├── __init__.py
├── config.py
├── data.py
├── estimator.py
├── metrics.py
├── model.py
└── trainer.py
```

## 2. 角色分工

### `config.py`

集中定义基于 Pydantic 的配置对象，通常包括：

- `DataConfig`
- `ModelConfig`
- `TrainerConfig`
- `EstimatorConfig`

让每个核心模块都有显式、可验证、可序列化的参数入口。

### `data.py`

负责数据集和数据准备逻辑。

优先包含：

- 面向当前数据形态的 dataset 对象。
- 必要的数据切分、张量化、批处理辅助逻辑。

不要为了通用化而提前做过重的数据框架。

### `model.py`

定义 `torch.nn.Module` 模型结构。

要求：

- 参数由 `ModelConfig` 驱动。
- 模型只负责前向与结构表达，不把训练循环塞进模块本身。

### `trainer.py`

负责训练、推理和测试循环。

通常应包含：

- `fit` 循环
- `predict` 或推理辅助逻辑
- `test` 或评估循环
- checkpoint 或日志保存的最小实现

训练控制逻辑放在这里，而不是塞进 estimator 或 model。

### `metrics.py`

优先使用 `torchmetrics`。

规则：

- 能直接用现成指标类时，优先复用。
- 没有合适指标时，再实现兼容 `torchmetrics` 风格的自定义类。

### `estimator.py`

这是整个方法的主入口，应表现得像 sklearn estimator，但不要求继承 sklearn 基类。

至少提供：

- `fit`
- `predict`

按任务需要提供：

- `predict_proba`
- `transform`

额外必须提供：

- `save`
- `load`（类方法）
- `test`

## 3. 组合方式

推荐让 estimator 组合其余三层逻辑：

- `data`
- `model`
- `trainer`

典型职责：

- estimator 负责统一对外接口。
- trainer 负责循环和调度。
- model 负责网络结构。
- data 负责数据入口。

这样能保持接口清晰，也更利于后续替换某一层实现。

## 4. `save` / `load` / `test` 约定

### `save`

保存当前模型所需的最小状态：

- model state dict
- 必要配置
- 恢复运行所需的关键元信息

### `load`

使用类方法恢复 estimator 实例，使用户可以像下面这样使用：

```python
estimator = MyEstimator.load(path)
```

### `test`

接受新数据集或数据加载器，返回结构清晰的评估结果，例如 `dict[str, float]`。

## 5. 导入与依赖边界

在 `src/<pkg>` 内优先使用相对导入，例如：

```python
from .config import EstimatorConfig
from .model import MyModel
```

在 `src/<pkg>_simulate` 与 `src/<pkg>_case` 内则优先使用绝对导入，例如：

```python
from <pkg>.estimator import MyEstimator
```

## 6. 保持最小可用

这套结构是为了让研究项目更清晰，不是为了引入框架负担。

因此：

- 不预埋用户没要的 callback/plugin/registry 系统。
- 不为了未来扩展而先写多层抽象基类。
- 不为了“像工业框架”而牺牲当前研究代码的可读性。

如果一个 50 行的直接实现就够用，就不要先写成 200 行框架。
