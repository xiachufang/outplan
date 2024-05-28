# ruff: noqa: PLR2004,E501
import random
import string
import time
from collections import defaultdict

import pytest

from outplan.client import ExperimentGroupClient
from outplan.exceptions import ExperimentValidateError
from outplan.experiment import ExperimentItem, GroupItem, NamespaceItem
from outplan.local import experiment_context

HomepageNamespace = NamespaceItem(
    name="namespace_1",
    experiment_items=[
        ExperimentItem(
            name="homepage_exp",
            bucket=9,
            group_items=[
                GroupItem(
                    name="imp",
                    layer_namespaces=[  # group by imp
                        NamespaceItem(
                            name="imp_ns_p9",
                            experiment_items=[
                                ExperimentItem(
                                    name="imp_p9",
                                    bucket=10,
                                    group_items=[
                                        GroupItem(name="p9-a0", weight=0.2),
                                        GroupItem(name="p9-a1", weight=0.8),
                                    ],
                                    pre_condition=lambda user_id, **ignore: user_id < 10,
                                )
                            ],
                        ),
                        NamespaceItem(
                            name="imp_ns_p8",
                            experiment_items=[
                                ExperimentItem(
                                    name="imp_p8",
                                    bucket=10,
                                    group_items=[
                                        GroupItem(name="p8-a0", weight=0.2),
                                        GroupItem(name="p8-a1", weight=0.6),
                                        GroupItem(name="p8-a2", weight=0.2),
                                    ],
                                    pre_condition=lambda user_id, **ignore: 10 <= user_id < 15,
                                )
                            ],
                        ),
                        NamespaceItem(
                            name="imp_ns_p7",
                            experiment_items=[
                                ExperimentItem(
                                    name="imp_p7",
                                    bucket=10,
                                    group_items=[
                                        GroupItem(name="p7-a0", weight=0.2),
                                        GroupItem(name="p7-a1", weight=0.6),
                                        GroupItem(name="p7-a2", weight=0.2),
                                    ],
                                    pre_condition=lambda user_id, **ignore: 15 <= user_id,
                                )
                            ],
                        ),
                    ],
                    weight=0.5,
                ),
                GroupItem(
                    name="collect",
                    layer_namespaces=[  # group by collect
                        NamespaceItem(
                            name="clt_ns_c9",
                            experiment_items=[
                                ExperimentItem(
                                    name="clt_p9",
                                    bucket=10,
                                    group_items=[
                                        GroupItem(name="c9-a0", weight=0.4),
                                        GroupItem(name="c9-a1", weight=0.6),
                                    ],
                                    pre_condition=lambda user_id, **ignore: user_id < 3,
                                )
                            ],
                        ),
                        NamespaceItem(
                            name="clt_ns_c8",
                            experiment_items=[
                                ExperimentItem(
                                    name="clt_p8",
                                    bucket=5,
                                    group_items=[
                                        GroupItem(
                                            name="c8-a0",
                                            layer_namespaces=[
                                                NamespaceItem(
                                                    name="clt_p8_ns",
                                                    experiment_items=[
                                                        ExperimentItem(
                                                            name="clt_p8_1",
                                                            bucket=10,
                                                            group_items=[
                                                                GroupItem(name="clt_p8_1_a0", weight=0.5),
                                                                GroupItem(name="clt_p8_1_a1", weight=0.5),
                                                            ],
                                                            pre_condition=lambda user_id, **ignore: user_id % 2 == 0,
                                                        )
                                                    ],
                                                ),
                                                NamespaceItem(
                                                    name="clt_p8_ns2",
                                                    experiment_items=[
                                                        ExperimentItem(
                                                            name="clt_p8_2",
                                                            bucket=10,
                                                            group_items=[
                                                                GroupItem(name="clt_p8_2_a0", weight=0.5),
                                                                GroupItem(
                                                                    name="clt_p8_2_a1",
                                                                    weight=0.5,
                                                                    extra_params="extra params",
                                                                ),
                                                            ],
                                                            pre_condition=lambda user_id, **ignore: user_id % 2 != 0,
                                                        )
                                                    ],
                                                ),
                                            ],
                                            weight=1,
                                        )
                                    ],
                                    pre_condition=lambda user_id, **ignore: 3 <= user_id < 20,
                                ),
                                ExperimentItem(
                                    name="clt_p8_2",
                                    bucket=5,
                                    group_items=[
                                        GroupItem(name="c8-b0", weight=0.4),
                                        GroupItem(name="c8-b1", weight=0.4),
                                        GroupItem(name="c8-b2", weight=0.2),
                                    ],
                                    pre_condition=lambda user_id, **ignore: 20 <= user_id,
                                ),
                            ],
                        ),
                    ],
                    weight=0.5,
                ),
            ],
        ),
        ExperimentItem(name="homepage_ctl", bucket=1, group_items=[GroupItem(name="h_ctl", weight=1)]),
    ],
)

GroupHookNamespace = NamespaceItem(
    name="group_hook_namespace",
    unit_type="user_id",
    experiment_items=[
        ExperimentItem(
            name="group_hook",
            bucket=10,
            group_items=[GroupItem(name="non_admin", weight=1), GroupItem(name="admin", weight=0)],
        )
    ],
)


namespace_spec_dict = {
    "name": "namespace_2",
    "bucket": 10,
    "unit_type": "pdid",
    "experiment_items": [
        {
            "name": "homepage_exp_2",
            "bucket": 9,
            "group_items": [
                {
                    "name": "imp_2",
                    "weight": 0.5,
                    "layer_namespaces": [
                        {
                            "name": "imp_ns_p9_2",
                            "experiment_items": [
                                {
                                    "name": "imp_p9_2",
                                    "bucket": 10,
                                    "group_items": [
                                        {"name": "p9-a0-2", "weight": 0.2},
                                        {"name": "p9-a1-2", "weight": 0.8},
                                    ],
                                    "pre_condition": "lambda user_id, **ignored: user_id < 10",
                                }
                            ],
                        },
                        {
                            "name": "imp_ns_p8_2",
                            "experiment_items": [
                                {
                                    "name": "imp_p8_2",
                                    "bucket": 10,
                                    "group_items": [
                                        {"name": "p8-a0-2", "weight": 0.2},
                                        {"name": "p8-a1-2", "weight": 0.6},
                                        {"name": "p8-a2-2", "weight": 0.2},
                                    ],
                                    "pre_condition": "lambda user_id, **ignored: 10 <= user_id < 15",
                                }
                            ],
                        },
                        {
                            "name": "imp_ns_p7_2",
                            "experiment_items": [
                                {
                                    "name": "imp_p7_2",
                                    "bucket": 10,
                                    "group_items": [
                                        {"name": "p7-a0-2", "weight": 0.2},
                                        {"name": "p7-a1-2", "weight": 0.6},
                                        {"name": "p7-a2-2", "weight": 0.2},
                                    ],
                                    "pre_condition": "lambda user_id, **ignored: 15 <= user_id",
                                }
                            ],
                        },
                    ],
                },
                {
                    "name": "collect_2",
                    "weight": 0.5,
                    "layer_namespaces": [
                        {
                            "name": "clt_ns_c9_2",
                            "experiment_items": [
                                {
                                    "name": "clt_p9_2",
                                    "bucket": 10,
                                    "group_items": [
                                        {"name": "c9-a0-2", "weight": 0.4},
                                        {"name": "c9-a1-2", "weight": 0.6},
                                    ],
                                    "pre_condition": "lambda user_id, **ignore: user_id < 3",
                                },
                            ],
                        },
                        {
                            "name": "clt_ns_c8_2",
                            "experiment_items": [
                                {
                                    "name": "clt_p8_2",
                                    "bucket": 5,
                                    "group_items": [
                                        {
                                            "name": "c8-a0-2",
                                            "weight": 1,
                                            "layer_namespaces": [
                                                {
                                                    "name": "clt_p8_ns_2",
                                                    "experiment_items": [
                                                        {
                                                            "name": "clt_p8_1_2",
                                                            "bucket": 10,
                                                            "group_items": [
                                                                {
                                                                    "name": "clt_p8_1_a0_2",
                                                                    "weight": 0.5,
                                                                },
                                                                {
                                                                    "name": "clt_p8_1_a1_2",
                                                                    "weight": 0.5,
                                                                },
                                                            ],
                                                            "pre_condition": "lambda user_id, **ignore: user_id % 2 == 0",
                                                        }
                                                    ],
                                                },
                                                {
                                                    "name": "clt_p8_ns2_2",
                                                    "experiment_items": [
                                                        {
                                                            "name": "clt_p8_2_2",
                                                            "bucket": 10,
                                                            "group_items": [
                                                                {
                                                                    "name": "clt_p8_2_a0_2",
                                                                    "weight": 0.5,
                                                                },
                                                                {
                                                                    "name": "clt_p8_2_a1_2",
                                                                    "weight": 0.5,
                                                                },
                                                            ],
                                                            "pre_condition": "lambda user_id, **ignore: user_id % 2 != 0",
                                                        }
                                                    ],
                                                },
                                            ],
                                        }
                                    ],
                                    "pre_condition": "lambda user_id, **ignore: user_id < 3",
                                },
                                {
                                    "name": "clt_p8_2_2",
                                    "bucket": 5,
                                    "group_items": [
                                        {"name": "c8-b0-2", "weight": 0.4},
                                        {"name": "c8-b1-2", "weight": 0.4},
                                        {"name": "c8-b2-2", "weight": 0.2},
                                    ],
                                },
                            ],
                        },
                    ],
                },
            ],
        },
        {
            "name": "homepage_ctl_2",
            "bucket": 1,
            "group_items": [{"name": "h_ctl_2", "weight": 1, "extra_params": "hahaha"}],
        },
    ],
}


def tag_filter(experiment_name, tag_id, device_id, **ignored):
    return device_id % 2 == 0


test_tag_namespace_spec_dict = dict(
    name="tag_spec",
    experiment_items=[
        dict(
            name="t1",
            bucket=10,
            group_items=[
                dict(
                    name="g1",
                    weight=1,
                    layer_namespaces=[
                        dict(
                            name="nn1",
                            experiment_items=[
                                dict(
                                    name="nn1e",
                                    bucket=10,
                                    user_tags=[dict(id=12, columns=["user_id"])],
                                    group_items=[
                                        dict(name="ngg", weight=0.5),
                                        dict(name="ngt", weight=0.5),
                                    ],
                                )
                            ],
                        ),
                        dict(
                            name="nn2",
                            experiment_items=[
                                dict(
                                    name="nn2e",
                                    bucket=10,
                                    user_tags=[dict(id=11, columns=["user_id"])],
                                    group_items=[
                                        dict(name="nag", weight=0.5),
                                        dict(name="nat", weight=0.5),
                                    ],
                                )
                            ],
                        ),
                    ],
                )
            ],
        )
    ],
)

TestTagNamespace = NamespaceItem(
    name="tag_it",
    experiment_items=[
        ExperimentItem(
            name="e1",
            bucket=10,
            group_items=[
                GroupItem(
                    name="g",
                    weight=1,
                    layer_namespaces=[
                        NamespaceItem(
                            name="n1",
                            experiment_items=[
                                ExperimentItem(
                                    name="n1e",
                                    bucket=10,
                                    user_tags=[dict(id=2, columns=["user_id"])],
                                    tag_filter_func=tag_filter,
                                    group_items=[
                                        GroupItem(name="gg", weight=0.5),
                                        GroupItem(name="gt", weight=0.5),
                                    ],
                                )
                            ],
                        ),
                        NamespaceItem(
                            name="n2",
                            experiment_items=[
                                ExperimentItem(
                                    name="n2e",
                                    bucket=10,
                                    user_tags=[dict(id=3, columns=["user_id"])],
                                    tag_filter_func=tag_filter,
                                    group_items=[
                                        GroupItem(name="ag", weight=0.5),
                                        GroupItem(name="at", weight=0.5),
                                    ],
                                )
                            ],
                        ),
                    ],
                )
            ],
        )
    ],
)


HomepageNamespace2 = NamespaceItem.from_dict(namespace_spec_dict)
TestTagNamespace2 = NamespaceItem.from_dict(test_tag_namespace_spec_dict, tag_filter_func=tag_filter)

AutoUpperUnitNamespace = NamespaceItem(
    name="auto_upper_namespace1",
    experiment_items=[
        ExperimentItem(
            name="auto_upper_experiment1",
            bucket=9,
            group_items=[
                GroupItem(
                    name="auto_upper_group1",
                    weight=0.5,
                ),
                GroupItem(
                    name="auto_upper_group2",
                    weight=0.5,
                ),
            ],
        )
    ],
    bucket=10,
    unit_type="pdid",
    auto_upper_unit=True,
)

auto_upper_namespace_spec_dict = {
    "name": "auto_upper_namespace2",
    "experiment_items": [
        {
            "name": "auto_upper_experiment2",
            "bucket": 9,
            "group_items": [
                {
                    "name": "auto_upper_group1",
                    "weight": 0.5,
                },
                {
                    "name": "auto_upper_group2",
                    "weight": 0.5,
                },
            ],
        },
    ],
    "bucket": 10,
    "unit_type": "pdid",
    "auto_upper_unit": True,
}

AutoUpperUnitNamespace2 = NamespaceItem.from_dict(auto_upper_namespace_spec_dict)

client = ExperimentGroupClient(
    [
        HomepageNamespace,
        HomepageNamespace2,
        TestTagNamespace,
        TestTagNamespace2,
        AutoUpperUnitNamespace,
        AutoUpperUnitNamespace2,
    ]
)


def test_experiment_group_client():
    # 两层嵌套
    group = client.get_tracking_group("namespace_1", unit="12345", user_id=1, track=False)
    assert (group.experiment_trace(), group.group_trace()) == (
        "homepage_exp.clt_p9",
        "collect.c9-a0",
    )
    group = client.get_group("namespace_1", unit="12345", user_id=1, track=False)
    assert group == "c9-a0"
    group = client.get_tracking_group("namespace_1", unit="12345asdfasdf", user_id=15, track=False)
    assert (group.experiment_trace(), group.group_trace()) == ("homepage_exp.imp_p7", "imp.p7-a1")
    group = client.get_tracking_group("namespace_1", unit="add", user_id=15, track=False)
    # 三层嵌套
    assert (group.experiment_trace(), group.group_trace()) == (
        "homepage_exp.clt_p8.clt_p8_2",
        "collect.c8-a0.clt_p8_2_a1",
    )
    assert group.group_extra_params == "extra params"

    group = client.get_tracking_group("namespace_2", unit="12345", user_id=1, track=False)
    assert (group.experiment_trace(), group.group_trace()) == (
        "homepage_exp_2.clt_p9_2",
        "collect_2.c9-a1-2",
    )
    group = client.get_group("namespace_2", unit="12345", user_id=1, track=False)
    assert group == "c9-a1-2"
    group = client.get_group("namespace_2", pdid="12345", user_id=1, track=False)
    assert group == "c9-a1-2"
    group = client.get_tracking_group("namespace_2", unit="12345asdfasdf", user_id=15, track=False)
    assert (group.experiment_trace(), group.group_trace()) == (
        "homepage_exp_2.clt_p8_2_2",
        "collect_2.c8-b0-2",
    )
    group = client.get_tracking_group("namespace_2", unit="add", user_id=15, track=False)
    # 三层嵌套
    assert (group.experiment_trace(), group.group_trace()) == ("homepage_ctl_2", "h_ctl_2")
    assert group.group_extra_params == "hahaha"

    group = client.get_tracking_group_by_group_name("namespace_2", "h_ctl_2")
    assert group.group_extra_params == "hahaha"


def test_lazy_load_namespace():
    lazy_load_cnt = defaultdict(int)

    def lazy_load_it(namespace):
        lazy_load_cnt[namespace] += 1
        return NamespaceItem.from_dict(namespace_spec_dict)

    def lazy_load_namespaces():
        lazy_load_cnt["lazy_load_namespaces"] += 1
        return ["namespace_2"]

    c = ExperimentGroupClient(
        [],
        lazy_load_namespaces_func=lazy_load_namespaces,
        lazy_load_namespace_item_func=lazy_load_it,
        lazy_load_expire=2,
    )
    group = c.get_tracking_group("namespace_2", unit="12345", user_id=1, track=False)
    assert (group.experiment_trace(), group.group_trace()) == (
        "homepage_exp_2.clt_p9_2",
        "collect_2.c9-a1-2",
    )

    assert lazy_load_cnt["namespace_2"] == 1
    assert lazy_load_cnt["lazy_load_namespaces"] == 1

    # flush cache
    group = c.get_tracking_group("namespace_2", unit="123456", user_id=1, track=False)
    assert (group.experiment_trace(), group.group_trace()) == (
        "homepage_exp_2.clt_p9_2",
        "collect_2.c9-a1-2",
    )

    assert lazy_load_cnt["namespace_2"] == 1
    assert lazy_load_cnt["lazy_load_namespaces"] == 1

    time.sleep(3)

    group = c.get_tracking_group("namespace_2", unit="123456", user_id=1, track=False)
    assert (group.experiment_trace(), group.group_trace()) == (
        "homepage_exp_2.clt_p9_2",
        "collect_2.c9-a1-2",
    )
    assert lazy_load_cnt["namespace_2"] == 2
    assert lazy_load_cnt["lazy_load_namespaces"] == 2

    # test lazy load
    with pytest.raises(ExperimentValidateError):
        c.get_tracking_group("namespace_4", unit="12345", user_id=1, track=False)


def test_experiment_context():
    # setup experiment context
    client.setup_experiment_context(user_id=1, device_id="12345")
    assert experiment_context.user_id == 1
    assert experiment_context.device_id == "12345"

    class MockTracker:
        times = 0

        def track(self, *args, **kwargs):
            MockTracker.times += 1

    client.tracking_client = MockTracker()

    with client.auto_group_by_device_id("namespace_1", user_id=1, track=False) as group:
        assert group == "c9-a0"

    with client.auto_group_by_device_id("namespace_1", cache=False, user_id=1, track=True) as group:
        assert group == "c9-a0"
    with client.auto_group_by_device_id("namespace_1", cache=True, user_id=1, track=True) as group:
        assert group == "c9-a0"
    assert MockTracker.times == 1

    experiment_context.release()
    with client.auto_group_by_device_id("namespace_1", user_id=1, track=False) as group:
        assert group is None

    client.setup_experiment_context(user_id=0, device_id="aaaa")
    with client.auto_group_by_user_id("namespace_1") as g:
        assert g

    # 空 unit 也打点
    assert MockTracker.times == 2
    client.setup_experiment_context(user_id=0, device_id="")
    with client.auto_group_by_user_id("namespace_1") as g:
        assert g

    assert MockTracker.times == 2

    client.setup_experiment_context(user_id=123, device_id="")
    with client.auto_group_by_device_id("namespace_1") as g:
        assert g

    assert MockTracker.times == 3
    client.release_context()


def test_experiment_tag():
    group = client.get_tracking_group("tag_it", 10, device_id=10)
    group2 = client.get_tracking_group("tag_spec", 10, device_id=10)
    assert (group.experiment_trace(), group.group_trace()) == ("e1.n1e", "g.gt")
    assert (group2.experiment_trace(), group2.group_trace()) == ("t1.nn1e", "g1.ngg")


def test_experiment_group_hook():
    def group_callback(context, namespace, uint, user_id, pdid):
        assert context.admin is not None
        if context.admin and user_id == 1:
            return "admin"

    c = ExperimentGroupClient([GroupHookNamespace], get_specified_group_func=group_callback)

    c.setup_experiment_context(allow_specify_group=True, admin=True)
    group = c.get_tracking_group("group_hook_namespace", unit="12345", user_id=1, pdid="233", track=False)
    assert group.group_names[0] == "admin"

    # unit_type & specify group
    group = c.get_tracking_group("group_hook_namespace", user_id=1, pdid="222", track=False)
    assert group.group_names[0] == "admin"

    c.setup_experiment_context(admin=False)
    group = c.get_tracking_group("group_hook_namespace", unit="12345", user_id=1, pdid="233", track=False)
    assert group.group_names[0] != "admin"


def test_not_full_bucket_namespace_get_group():
    namespace_spec = {
        "name": "not_full_namespace",
        "bucket": 1000,
        "unit_type": "pdid",
        "experiment_items": [
            {
                "name": "homepage_ctl",
                "bucket": 1,
                "group_items": [{"name": "h_ctl_2", "weight": 1, "extra_params": "hahaha"}],
            },
        ],
    }
    namespace = NamespaceItem.from_dict(namespace_spec)
    namespace.validate()

    cnt = 0
    while cnt <= 10 and namespace.get_group(unit=f"foo-{cnt}") is not None:
        cnt += 1
    assert cnt <= 10

    namespace_spec = {
        "name": "not_full_namespace",
        "bucket": 1000,
        "unit_type": "pdid",
        "experiment_items": [
            {
                "name": "homepage_ctl",
                "bucket": 999,
                "group_items": [{"name": "h_ctl_2", "weight": 1, "extra_params": "hahaha"}],
            },
        ],
    }
    namespace = NamespaceItem.from_dict(namespace_spec)
    namespace.validate()

    cnt = 0
    while cnt <= 10 and namespace.get_group(unit=f"foo-{cnt}") is None:
        cnt += 1
    assert cnt <= 10


def test_nested_not_full_experiment_group_client():
    """
    测试实验组嵌套子namespace，并且子 namespace 中实验 bucket 不满的情况
    """
    namespace_spec = {
        "name": "test_namespace_exp2",
        "bucket": 100,
        "unit_type": "pdid",
        "auto_upper_unit": True,
        "experiment_items": [
            {
                "name": "ttt111",
                "bucket": 50,
                "pre_condition": "",
                "group_items": [
                    {
                        "name": "ns1",
                        "weight": 0.33,
                        "extra_params": "",
                        "layer_namespaces": [
                            {
                                "name": "nested_ns1",
                                "bucket": 100,
                                "unit_type": "pdid",
                                "auto_upper_unit": True,
                                "experiment_items": [
                                    {
                                        "name": "nested_test_1",
                                        "bucket": 10,
                                        "pre_condition": "",
                                        "group_items": [
                                            {
                                                "name": "exp1",
                                                "weight": 0.5,
                                                "extra_params": "",
                                                "layer_namespaces": [],
                                            },
                                            {
                                                "name": "control1",
                                                "weight": 0.5,
                                                "extra_params": "",
                                                "layer_namespaces": [],
                                            },
                                        ],
                                        "user_tags": [],
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "name": "ns2",
                        "weight": 0.34,
                        "extra_params": "",
                        "layer_namespaces": [
                            {
                                "name": "nested_test_ns2",
                                "bucket": 100,
                                "unit_type": "pdid",
                                "auto_upper_unit": True,
                                "experiment_items": [
                                    {
                                        "name": "nested_test_0528_2",
                                        "bucket": 20,
                                        "pre_condition": "",
                                        "group_items": [
                                            {
                                                "name": "exp2",
                                                "weight": 0.5,
                                                "extra_params": "",
                                                "layer_namespaces": [],
                                            },
                                            {
                                                "name": "control2",
                                                "weight": 0.5,
                                                "extra_params": "",
                                                "layer_namespaces": [],
                                            },
                                        ],
                                        "user_tags": [],
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "name": "ns3",
                        "weight": 0.33,
                        "extra_params": "",
                        "layer_namespaces": [
                            {
                                "name": "test_nested_0528_3",
                                "bucket": 100,
                                "unit_type": "pdid",
                                "auto_upper_unit": True,
                                "experiment_items": [
                                    {
                                        "name": "test_nested_0528_3",
                                        "bucket": 30,
                                        "pre_condition": "",
                                        "group_items": [
                                            {
                                                "name": "exp3",
                                                "weight": 0.5,
                                                "extra_params": "",
                                                "layer_namespaces": [],
                                            },
                                            {
                                                "name": "control3",
                                                "weight": 0.5,
                                                "extra_params": "",
                                                "layer_namespaces": [],
                                            },
                                        ],
                                        "user_tags": [],
                                    }
                                ],
                            }
                        ],
                    },
                ],
                "user_tags": [],
            },
            {
                "name": "test_nest_0528_4",
                "bucket": 50,
                "pre_condition": "",
                "group_items": [
                    {
                        "name": "a",
                        "weight": 0.5,
                        "extra_params": "",
                        "layer_namespaces": [],
                    },
                    {
                        "name": "control",
                        "weight": 0.5,
                        "extra_params": "",
                        "layer_namespaces": [],
                    },
                ],
                "user_tags": [],
            },
        ],
    }
    namespace = NamespaceItem.from_dict(namespace_spec)
    namespace.validate()

    for i in range(1000):
        namespace.get_group(unit=f"foo-{i}")

    expected = ['a', None, 'control', 'a', None, 'control', 'a', None, 'a', 'control', 'exp1', 'control3', 'control', None, 'control3', None, 'exp3', 'a', None, None]

    for i in range(20):
        res = namespace.get_group(unit=f"foo-{i}")
        if res:
            assert res.last_group == expected[i]
        else:
            assert expected[i] is None


def test_auto_upper_unit_namespace():
    def same_group(group_a, group_b):
        if group_a is None and group_b is None:
            return True
        if group_a is None or group_b is None:
            return False
        return (
            group_a.experiment_trace() == group_b.experiment_trace() and group_a.group_trace() == group_b.group_trace()
        )

    # test auto_upper_namespace1
    assert same_group(
        client.get_tracking_group("auto_upper_namespace1", unit="abc-12345"),
        client.get_tracking_group("auto_upper_namespace1", unit="ABC-12345"),
    )

    for _ in range(100):
        rand_pdid = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        assert same_group(
            client.get_tracking_group("auto_upper_namespace1", unit=rand_pdid),
            client.get_tracking_group("auto_upper_namespace1", unit=rand_pdid.upper()),
        )

    # test auto_upper_namespace2
    assert same_group(
        client.get_tracking_group("auto_upper_namespace2", unit="abc-12345"),
        client.get_tracking_group("auto_upper_namespace2", unit="ABC-12345"),
    )

    for _ in range(100):
        rand_pdid = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        assert same_group(
            client.get_tracking_group("auto_upper_namespace2", unit=rand_pdid),
            client.get_tracking_group("auto_upper_namespace2", unit=rand_pdid.upper()),
        )

    # test normal namespace
    res = []
    for _ in range(1000):
        rand_pdid = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        res.append(
            same_group(
                client.get_tracking_group("namespace_1", unit=rand_pdid),
                client.get_tracking_group("namespace_1", unit=rand_pdid.upper()),
            )
        )
    assert not all(res)
