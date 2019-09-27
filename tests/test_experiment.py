# coding: utf-8

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
                GroupItem(name="imp", layer_namespaces=[  # group by imp
                    NamespaceItem(name="imp_ns_p9", experiment_items=[
                        ExperimentItem(name="imp_p9", bucket=10, group_items=[
                            GroupItem(name="p9-a0", weight=0.2),
                            GroupItem(name="p9-a1", weight=0.8),
                        ], pre_condition=lambda user_id, **ignore: user_id < 10)
                    ]),
                    NamespaceItem(name="imp_ns_p8", experiment_items=[
                        ExperimentItem(name="imp_p8", bucket=10, group_items=[
                            GroupItem(name="p8-a0", weight=0.2),
                            GroupItem(name="p8-a1", weight=0.6),
                            GroupItem(name="p8-a2", weight=0.2),
                        ], pre_condition=lambda user_id, **ignore: 10 <= user_id < 15)
                    ]),
                    NamespaceItem(name="imp_ns_p7", experiment_items=[
                        ExperimentItem(name="imp_p7", bucket=10, group_items=[
                            GroupItem(name="p7-a0", weight=0.2),
                            GroupItem(name="p7-a1", weight=0.6),
                            GroupItem(name="p7-a2", weight=0.2),
                        ], pre_condition=lambda user_id, **ignore: 15 <= user_id)
                    ])
                ], weight=0.5),
                GroupItem(name="collect", layer_namespaces=[  # group by collect
                    NamespaceItem(name="clt_ns_c9", experiment_items=[
                        ExperimentItem(name="clt_p9", bucket=10, group_items=[
                            GroupItem(name="c9-a0", weight=0.4),
                            GroupItem(name="c9-a1", weight=0.6),
                        ], pre_condition=lambda user_id, **ignore: user_id < 3)
                    ]),
                    NamespaceItem(name="clt_ns_c8", experiment_items=[
                        ExperimentItem(name="clt_p8", bucket=5, group_items=[
                            GroupItem(name="c8-a0", layer_namespaces=[
                                NamespaceItem(name="clt_p8_ns", experiment_items=[
                                    ExperimentItem(name="clt_p8_1", bucket=10, group_items=[
                                        GroupItem(name="clt_p8_1_a0", weight=0.5),
                                        GroupItem(name="clt_p8_1_a1", weight=0.5),
                                    ], pre_condition=lambda user_id, **ignore: user_id % 2 == 0)
                                ]),
                                NamespaceItem(name="clt_p8_ns2", experiment_items=[
                                    ExperimentItem(name="clt_p8_2", bucket=10, group_items=[
                                        GroupItem(name="clt_p8_2_a0", weight=0.5),
                                        GroupItem(name="clt_p8_2_a1", weight=0.5, extra_params="extra params"),
                                    ], pre_condition=lambda user_id, **ignore: user_id % 2 != 0)
                                ])
                            ], weight=1)
                        ], pre_condition=lambda user_id, **ignore: 3 <= user_id < 20),
                        ExperimentItem(name="clt_p8_2", bucket=5, group_items=[
                            GroupItem(name="c8-b0", weight=0.4),
                            GroupItem(name="c8-b1", weight=0.4),
                            GroupItem(name="c8-b2", weight=0.2),
                        ], pre_condition=lambda user_id, **ignore: 3 <= user_id < 20),
                    ])
                ], weight=0.5)

            ]
        ),
        ExperimentItem(
            name="homepage_ctl",
            bucket=1,
            group_items=[
                GroupItem(name="h_ctl", weight=1)
            ]
        )
    ]
)

GroupHookNamespace = NamespaceItem(
    name="group_hook_namespace",
    experiment_items=[
        ExperimentItem(
            name="group_hook",
            bucket=10,
            group_items=[
                GroupItem(name="non_admin", weight=1),
                GroupItem(name="admin", weight=0)
            ]
        )
    ]
)


namespace_spec_dict = {
    "name": "namespace_2",
    "bucket": 10,
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
                                    "pre_condition": "lambda user_id, **ignored: user_id < 10"
                                }
                            ]
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
                                    "pre_condition": "lambda user_id, **ignored: 10 <= user_id < 15"
                                }
                            ]
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
                                    "pre_condition": "lambda user_id, **ignored: 15 <= user_id"
                                }
                            ]
                        },
                    ]
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
                            ]
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
                                                                {"name": "clt_p8_1_a0_2", "weight": 0.5},
                                                                {"name": "clt_p8_1_a1_2", "weight": 0.5},
                                                            ],
                                                            "pre_condition": "lambda user_id, **ignore: user_id % 2 == 0"
                                                        }
                                                    ]
                                                },
                                                {
                                                    "name": "clt_p8_ns2_2",
                                                    "experiment_items": [
                                                        {
                                                            "name": "clt_p8_2_2",
                                                            "bucket": 10,
                                                            "group_items": [
                                                                {"name": "clt_p8_2_a0_2", "weight": 0.5},
                                                                {"name": "clt_p8_2_a1_2", "weight": 0.5},
                                                            ],
                                                            "pre_condition": "lambda user_id, **ignore: user_id % 2 != 0"
                                                        }
                                                    ]
                                                }
                                            ]
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
                                    ]
                                }
                            ]
                        },
                    ]
                }
            ]
        },
        {
            "name": "homepage_ctl_2",
            "bucket": 1,
            "group_items": [
                {"name": "h_ctl_2", "weight": 1, "extra_params": "hahaha"}
            ]
        }
    ]
}


def tag_filter(experiment_name, tag_id, device_id, **ignored):
    return device_id % 2 == 0


test_tag_namespace_spec_dict = dict(
    name="tag_spec",
    experiment_items=[
        dict(name="t1", bucket=10, group_items=[
            dict(name="g1", weight=1, layer_namespaces=[
                dict(name="nn1", experiment_items=[dict(
                    name="nn1e", bucket=10, user_tags=[dict(id=12, columns=['user_id'])], group_items=[
                        dict(name="ngg", weight=0.5),
                        dict(name="ngt", weight=0.5),
                    ]
                )]),
                dict(name="nn2", experiment_items=[dict(
                    name="nn2e", bucket=10, user_tags=[dict(id=11, columns=['user_id'])], group_items=[
                        dict(name="nag", weight=0.5),
                        dict(name="nat", weight=0.5),
                    ]
                )]),
            ])
        ])
    ]
)

TestTagNamespace = NamespaceItem(name="tag_it", experiment_items=[
    ExperimentItem(name="e1", bucket=10, group_items=[
        GroupItem(name="g", weight=1, layer_namespaces=[
            NamespaceItem(name="n1", experiment_items=[ExperimentItem(
                name="n1e", bucket=10, user_tags=[dict(id=2, columns=['user_id'])], tag_filter_func=tag_filter, group_items=[
                    GroupItem(name="gg", weight=0.5),
                    GroupItem(name="gt", weight=0.5),
                ]
            )]),
            NamespaceItem(name="n2", experiment_items=[ExperimentItem(
                name="n2e", bucket=10, user_tags=[dict(id=3, columns=['user_id'])], tag_filter_func=tag_filter, group_items=[
                    GroupItem(name="ag", weight=0.5),
                    GroupItem(name="at", weight=0.5),
                ]
            )]),
        ])
    ])
])


HomepageNamespace2 = NamespaceItem.from_dict(namespace_spec_dict)
TestTagNamespace2 = NamespaceItem.from_dict(test_tag_namespace_spec_dict, tag_filter_func=tag_filter)

client = ExperimentGroupClient([HomepageNamespace, HomepageNamespace2, TestTagNamespace, TestTagNamespace2])


def test_experiment_group_client():
    # 两层嵌套
    group = client.get_tracking_group('namespace_1', unit="12345", user_id=1, track=False)
    assert (group.experiment_trace(), group.group_trace()) == ('homepage_exp.clt_p9', 'collect.c9-a0')
    group = client.get_group('namespace_1', unit="12345", user_id=1, track=False)
    assert group == "c9-a0"
    group = client.get_tracking_group('namespace_1', unit="12345asdfasdf", user_id=15, track=False)
    assert (group.experiment_trace(), group.group_trace()) == ('homepage_exp.imp_p7', 'imp.p7-a1')
    group = client.get_tracking_group('namespace_1', unit="add", user_id=15, track=False)
    # 三层嵌套
    assert (group.experiment_trace(), group.group_trace()) == ('homepage_exp.clt_p8.clt_p8_2', 'collect.c8-a0.clt_p8_2_a1')
    assert group.group_extra_params == "extra params"

    group = client.get_tracking_group('namespace_2', unit="12345", user_id=1, track=False)
    assert (group.experiment_trace(), group.group_trace()) == ('homepage_exp_2.clt_p9_2', 'collect_2.c9-a1-2')
    group = client.get_group('namespace_2', unit="12345", user_id=1, track=False)
    assert group == "c9-a1-2"
    group = client.get_tracking_group('namespace_2', unit="12345asdfasdf", user_id=15, track=False)
    assert (group.experiment_trace(), group.group_trace()) == ('homepage_exp_2.clt_p8_2_2', 'collect_2.c8-b0-2')
    group = client.get_tracking_group('namespace_2', unit="add", user_id=15, track=False)
    # 三层嵌套
    assert (group.experiment_trace(), group.group_trace()) == ('homepage_ctl_2', 'h_ctl_2')
    assert group.group_extra_params == "hahaha"

    group = client.get_tracking_group_by_group_name('namespace_2', 'h_ctl_2')
    assert group.group_extra_params == "hahaha"


def test_lazy_load_namespace():
    def lazy_load_it(namespace):
        return NamespaceItem.from_dict(namespace_spec_dict)

    c = ExperimentGroupClient([], lazy_load_namespaces=['namespace_2'], lazy_load_func=lazy_load_it)
    group = c.get_tracking_group('namespace_2', unit="12345", user_id=1, track=False)
    assert (group.experiment_trace(), group.group_trace()) == ('homepage_exp_2.clt_p9_2', 'collect_2.c9-a1-2')

    with pytest.raises(ExperimentValidateError):
        group = c.get_tracking_group('namespace_4', unit="12345", user_id=1, track=False)


def test_experiment_context():
    # setup experiment context
    client.setup_experiment_context(user_id=1, device_id="12345")
    assert experiment_context.user_id == 1
    assert experiment_context.device_id == "12345"
    with client.auto_group_by_device_id("namespace_1", user_id=1, track=False) as group:
        assert group == "c9-a0"

    experiment_context.release()
    with client.auto_group_by_device_id("namespace_1", user_id=1, track=False) as group:
        assert group is None


def test_experiment_tag():
    group = client.get_tracking_group("tag_it", 10, device_id=10)
    group2 = client.get_tracking_group("tag_spec", 10, device_id=10)
    assert (group.experiment_trace(), group.group_trace()) == ("e1.n1e", "g.gt")
    assert (group2.experiment_trace(), group2.group_trace()) == ("t1.nn1e", "g1.ngg")


def test_experiment_group_hook():
    def group_callback(context, namespace, user_id, pdid):
        assert context.admin is not None
        if context.admin and user_id == 1:
            return 'admin'
    c = ExperimentGroupClient([GroupHookNamespace], get_group_hook=group_callback)

    c.setup_experiment_context(admin=True)
    group = c.get_tracking_group('group_hook_namespace', unit="12345", user_id=1, pdid='233', track=False)
    assert group.group_names[0] == 'admin'

    c.setup_experiment_context(admin=False)
    group = c.get_tracking_group('group_hook_namespace', unit="12345", user_id=1, pdid="233", track=False)
    assert group.group_names[0] != "admin"
