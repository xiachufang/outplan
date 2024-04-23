# outplan

[![Build Status](https://travis-ci.com/xiachufang/outplan.svg?branch=master)](https://travis-ci.com/xiachufang/outplan) ![GitHub](https://img.shields.io/github/license/xiachufang/outplan)

Support nested experiment/namespace base on [PlanOut](https://github.com/facebook/planout)

# Install
```python
pip install outplan
```

# Usage

```python
from outplan import NamespaceItem, ExperimentItem, GroupItem, ExperimentGroupClient

SimpleNamespace = NamespaceItem(
    name="namespace_1",
    bucket=10,
    experiment_items=[
        ExperimentItem(
            name="exp_1",
            bucket=10,
            group_items=[
                GroupItem(name="a", weight=0.5),
                GroupItem(name="b", weight=0.5),
            ]
        ),
    ]
)

client = ExperimentGroupClient([SimpleNamespace])

print(client.get_group("namespace_1", unit="your_unit"))


# nested experiment/namespace is defined at `tests/test_experiment.py`
```

# Dev

```shell
# install deps (once)
pip install -e .[test]

# run test
make test

# commit
pip install pre-commit
# and commit here
```
