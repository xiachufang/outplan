# coding: utf-8
from collections import namedtuple
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional

import simplejson
from planout.experiment import DefaultExperiment
from planout.namespace import SimpleNamespace
from planout.ops.random import WeightedChoice

from .const import GroupResultType, UserTagFilterType
from .exceptions import ExperimentGroupNotFindError, ExperimentValidateError


class TrackingGroup(object):
    """Group object with group trace info"""

    def __init__(self, group_name=None, experiment_name=None, group_extra_params=None):
        self.group_names = []
        self.experiment_names = []
        self.group_extra_params = group_extra_params
        if group_name:
            self.group_names.append(group_name)

        if experiment_name:
            self.experiment_names.append(experiment_name)

    def add_group_name(self, group_name):
        self.group_names.append(group_name)

    def add_experiment_name(self, exp_name):
        self.experiment_names.append(exp_name)

    def group_trace(self):
        """分组名链"""
        return ".".join(reversed(self.group_names))

    def experiment_trace(self):
        """实验链"""
        return ".".join(reversed(self.experiment_names))

    @property
    def last_group(self):
        """最后一个分组名"""
        return self.group_names and self.group_names[0]

    @property
    def last_experiment(self):
        # type: () -> str
        """最后一个实验名"""
        return self.experiment_names and self.experiment_names[0]


def generate_planout_experiment(experiment_item):
    # type: (ExperimentItem) -> DefaultExperiment

    class _PlanoutExperiment(DefaultExperiment):
        def assign(self, params, unit, **kwargs):
            params.group = WeightedChoice(
                choices=experiment_item.group_items,
                weights=[group.weight for group in experiment_item.group_items],
                unit=unit
            )
            params.experiment_name = experiment_item.name

    return _PlanoutExperiment


def generate_planout_namespace(namespace_item, valid_experiment_items):
    # type: (NamespaceItem, List[ExperimentItem]) -> SimpleNamespace

    class _PlanoutNamespace(SimpleNamespace):
        def setup(self):
            self.name = namespace_item.name
            self.primary_unit = namespace_item.unit
            self.num_segments = namespace_item.bucket

        def setup_experiments(self):
            for experiment_item in valid_experiment_items:
                self.add_experiment(
                    experiment_item.name,
                    generate_planout_experiment(experiment_item),
                    experiment_item.bucket
                )

    return _PlanoutNamespace


def get_namespace_group_names(namespace_item):
    """取该 namespace 下的所有分组 ID 和 name"""
    names = []
    for experiment_item in namespace_item.experiment_items:
        for group_item in experiment_item.group_items:
            names.append(group_item.name)
            for namespace in group_item.layer_namespaces:
                _names = get_namespace_group_names(namespace)
                names.extend(_names)

    return names


class NamespaceItem(object):
    """一个 namespace 对应一个总体，里面可以有多个实验，
    但如果多个实验影响同一个结果，则多个实验必须处于同一个 namespace
    """

    def __init__(self, name, experiment_items, bucket=10, unit="unit"):
        if not all([name, experiment_items]):
            raise ValueError("Namespace name and experiment_items required.")

        self.name = name
        self.experiment_items = experiment_items    # type: List[ExperimentItem]
        self.bucket = bucket
        self.unit = unit

        self.validate()

    def validate(self):
        experiment_total_bucket = 0
        experiment_names = set()
        for experiment_item in self.experiment_items:

            experiment_total_bucket += experiment_item.bucket

            if experiment_item.name in experiment_names:
                raise ExperimentValidateError(u"experiment name: {} 重复".format(experiment_item.name))

            experiment_names.add(experiment_item.name)

        if experiment_total_bucket != self.bucket:
            raise ExperimentValidateError(u"实验({})总 bucket 数必须与 namespace bucket 相等".format(self.name))

        # 同一个 namespace 下的 group name 必须唯一
        group_names = get_namespace_group_names(self)

        if len(group_names) != len(set(group_names)):
            raise ExperimentValidateError("实验({}) group name 重复".format(self.name))

    def get_group(self, unit, **params):
        valid_experiment_items = []
        for experiment_item in self.experiment_items:
            if callable(experiment_item.pre_condition):
                if not experiment_item.pre_condition(**params):
                    continue

            if experiment_item.user_tags and experiment_item.tag_filter_func:
                res = None
                # 多个标签为 AND 关系
                if experiment_item.tag_filter_type == UserTagFilterType.AND:
                    res = True
                    for user_tag in experiment_item.user_tags:
                        _res = experiment_item.tag_filter_func(experiment_item.name, user_tag.tag_id, user_tag_columns=user_tag.columns, **params)
                        if user_tag.not_in:
                            _res = not _res

                        res &= _res
                        if not res:
                            break
                # 多个标签为 OR 关系
                elif experiment_item.tag_filter_type == UserTagFilterType.OR:
                    res = False
                    for user_tag in experiment_item.user_tags:
                        _res = experiment_item.tag_filter_func(experiment_item.name, user_tag.tag_id, user_tag_columns=user_tag.columns, **params)
                        if user_tag.not_in:
                            _res = not _res

                        res |= _res
                        if res:
                            break

                if not res:
                    continue

            valid_experiment_items.append(experiment_item)

        if not valid_experiment_items:
            return None

        planout_namespace_cls = generate_planout_namespace(self, valid_experiment_items)
        res = planout_namespace_cls(unit=unit, **params)
        group_item = res.get('group')

        group_names, exp_names = [group_item.name], [res.get('experiment_name')]
        if group_item.result_type == GroupResultType.group:
            return TrackingGroup(
                group_name=group_item.name,
                experiment_name=res.get('experiment_name'),
                group_extra_params=group_item.extra_params
            )
        elif group_item.result_type == GroupResultType.layer:

            # 直到取到最底层分组
            while True:
                _res = group_item.get_group(unit, **params)
                if isinstance(_res, TrackingGroup):
                    for group_name, exp_name in zip(group_names, exp_names):
                        _res.add_group_name(group_name)
                        _res.add_experiment_name(exp_name)
                    return _res
                else:
                    group_names.append(_res.get('group').name)
                    exp_names.append(_res.get('experiment_name'))
        else:
            raise NotImplementedError()

    @classmethod
    def from_json(cls, json_namespace, tag_filter_func=None):
        # type: (str, Optional[Callable]) -> NamespaceItem

        if not json_namespace:
            raise ExperimentValidateError("json_namespace required.")

        namespace_spec = simplejson.loads(json_namespace)
        return cls.from_dict(namespace_spec, tag_filter_func=tag_filter_func)

    @classmethod
    def from_dict(cls, data, tag_filter_func=None):
        # type: (Dict[str, Any], Optional[Callable]) -> NamespaceItem
        return cls(
            name=data['name'],
            bucket=int(data.get('bucket', 10)),
            experiment_items=[ExperimentItem.from_dict(spec, tag_filter_func) for spec in data['experiment_items']],
        )


class ExperimentItem(object):
    """实验类"""

    def __init__(self, name, bucket, group_items, pre_condition=None, user_tags=None, tag_filter_func=None):
        self.name = name
        self.bucket = bucket
        self.group_items = group_items
        self.pre_condition = pre_condition
        self.tag_filter_type = UserTagFilterType.AND    # 多个 tag_ids 为 and 关系
        self.tag_filter_func = tag_filter_func

        try:
            self.user_tags = self._parse_user_tag(user_tags)
        except Exception as e:
            raise ExperimentValidateError("实验({})标签格式错误:{}".format(self.name, str(e)))

        self.validate()

    def validate(self):
        group_names = set()
        for group_item in self.group_items:
            if group_item.name in group_names:
                raise ExperimentValidateError("group_name {} 冲突".format(group_item.name))

            group_names.add(group_item.name)

        if sum([Decimal(str(group.weight)) for group in self.group_items]) != 1:
            raise ExperimentValidateError("实验({}) 分组的 weight 总数不为 1".format(self.name))

    @classmethod
    def from_dict(cls, data, tag_filter_func=None):
        # type: (Dict[str, Any], Optional[Callable]) -> ExperimentItem
        return cls(
            name=data['name'],
            bucket=int(data['bucket']),
            group_items=[GroupItem.from_dict(spec) for spec in data['group_items']],
            pre_condition=eval(data['pre_condition']) if data.get('pre_condition') else None,
            tag_filter_func=tag_filter_func,
            user_tags=data.get('user_tags', []),
        )

    @classmethod
    def _parse_user_tag(cls, user_tags):
        """解析 user_tags 信息

        :param user_tags: 实验指定的用户标签
        """
        UserTag = namedtuple("UserTag", ["tag_id", "columns", "not_in"])
        if not user_tags:
            return []

        res = []
        for user_tag in user_tags:
            res.append(UserTag(
                tag_id=user_tag['id'],
                columns=user_tag['columns'],
                not_in=user_tag.get('not_in', False)    # not_in 表示该标签的互斥，不在该标签里
            ))

        return res


class GroupItem(object):
    def __init__(self, name, weight, layer_namespaces=None, extra_params=None):
        self.name = name
        self.weight = weight
        self.layer_namespaces = layer_namespaces or []
        self.result_type = None
        self.extra_params = extra_params

        self.validate()

    def validate(self):
        # 分层
        if self.layer_namespaces:
            self.result_type = GroupResultType.layer
            namespace_names = set()
            for namespace_item in self.layer_namespaces:
                if namespace_item.name in namespace_names:
                    raise ExperimentValidateError("namespace name({}) 冲突".format(namespace_item.name))

                namespace_names.add(namespace_item.name)
        # 分组
        else:
            self.result_type = GroupResultType.group
            if self.weight > 1:
                raise ExperimentValidateError("group weight({}) 必须小于等于 1".format(self.name))

    def get_group(self, unit, **params):
        if self.result_type == GroupResultType.group:
            return self.name
        elif self.result_type == GroupResultType.layer:
            # 这里所有复制出来的 namespace 只有一个返回 group
            for namespace in self.layer_namespaces:
                _group = namespace.get_group(unit, **params)
                if _group:
                    return _group
        else:
            raise NotImplementedError()

        raise ExperimentGroupNotFindError("未找到分组")

    @classmethod
    def from_dict(cls, data):
        # type: (Dict[str, Any]) -> GroupItem
        return cls(
            name=data['name'],
            weight=float(data['weight']),
            layer_namespaces=[NamespaceItem.from_dict(spec) for spec in data.get('layer_namespaces', [])],
            extra_params=data.get('extra_params')
        )
