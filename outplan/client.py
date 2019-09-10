# coding: utf-8

from .exceptions import ExperimentValidateError
from .local import experiment_context
from contextlib import contextmanager


class ExperimentGroupClient(object):
    """experiment group client"""

    def __init__(self, namespaces_items, tracking_client=None, logger=None):
        # type: (List[NamespaceItem]) -> None

        self.namespaces_items = namespaces_items
        self.namespaces = {namespace.name: namespace for namespace in namespaces_items}
        self.tracking_client = tracking_client
        self.logger = logger

    def validate(self):
        names = set()
        for namespace in self.namespaces_items:
            if namespace.name in names:
                raise ExperimentValidateError("namespace name 冲突")

            names.add(namespace.name)

    def get_tracking_group(self, namespace_name, unit, user_id=None, pdid=None, track=True, **params):
        # type: (NamespaceItem, str) -> Any
        """取分组的全局唯一标识符，带上实验链的信息"""
        if namespace_name not in self.namespaces:
            raise ExperimentValidateError("Namespace name not found.")

        tracking_group = self.namespaces[namespace_name].get_group(unit, user_id=user_id, pdid=pdid, **params)
        if not track or not any([user_id, pdid]) or not self.tracking_client:
            return tracking_group

        self.tracking_client.track(
            user_id=user_id or 0,
            pdid=pdid or "",
            event_name="user_experiment_group_info",
            properties=dict(
                experiment=tracking_group.experiment_trace(),
                group=tracking_group.group_trace(),
            )
        )
        return tracking_group

    def get_group(self, namespace_name, unit, user_id=None, pdid=None, track=True, **params):
        return self.get_tracking_group(namespace_name, unit, user_id, pdid, track, **params).group_names[0]

    def add_namespace(self, namespace_item):
        # type: (NamespaceItem) -> None
        if namespace_item.name in self.namespaces:
            raise ExperimentValidateError("namespace name 冲突")

        self.namespaces[namespace_item.name] = namespace_item

    def setup_experiment_context(self, user_id=None, device_id=None, origin=None, version=None):
        experiment_context.user_id = user_id
        experiment_context.device_id = device_id
        experiment_context.origin = origin
        experiment_context.version = version

    def release_context(self):
        experiment_context.release()

    @contextmanager
    def auto_group_by_device_id(self, namespace_name, **params):
        """使用 experiment_context 自动取设备 ID 分组。

        Example:

            >>> with self.auto_group_by_device_id("namespace") as group:
            >>>     if group is None:
            >>>         group = Group.control   # fallback 到 control 组

            >>>     if group == Group.a:
            >>>         return "it's a"
            >>>     elif group == Group.control:
            >>>         return "it's control"
        """
        try:
            device_id = experiment_context.device_id
            yield self.get_group(namespace_name, unit=device_id, device_id=device_id, **params)
        except AttributeError as e:
            # 这里需要被 fallback 到 control 组
            if self.logger:
                self.logger.error(
                    "auto_group error: namespace_name: {}, msg: {}, params: {}",
                    namespace_name, str(e), simplejson.dumps(params)
                )
            yield None

    @contextmanager
    def auto_group_by_user_id(self, namespace_name, **params):
        try:
            user_id = experiment_context.user_id
            yield self.get_group(namespace_name, unit=user_id, user_id=user_id, **params)
        except AttributeError as e:
            # 这里需要被 fallback 到 control 组
            if self.logger:
                self.logger.error(
                    "auto_group error: namespace_name: {}, msg: {}, params: {}",
                    namespace_name, str(e), simplejson.dumps(params)
                )
            yield None
