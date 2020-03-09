# coding: utf-8

import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional

import simplejson

from .const import ONE_MINUTE
from .exceptions import ExperimentValidateError
from .experiment import NamespaceItem, TrackingGroup
from .local import experiment_context


class ExperimentGroupClient(object):
    """experiment group client"""

    def __init__(self, namespaces_items, lazy_load_namespaces_func=None, lazy_load_namespace_item_func=None,
                 tracking_client=None, logger=None,
                 lazy_load_expire=10 * ONE_MINUTE, get_specified_group_func=None):
        # type: (List[NamespaceItem], Optional[List[str]], Callable, Any, Any, int, Callable) -> None

        self.namespaces_items = namespaces_items
        self.namespaces = {namespace.name: namespace for namespace in namespaces_items}
        self.tracking_client = tracking_client
        self.logger = logger
        self.lazy_load_namespaces = []  # type: List[str]
        self.lazy_load_expire = lazy_load_expire
        self._lazy_load_init_ts = {}    # type: Dict[str, int]  # 记录 lazy load 的 namespace 初始化时间，expire 之后重新 load
        self.lazy_load_namespace_items = {}     # type: Dict[str, NamespaceItem]
        self.lazy_load_namespace_item_func = lazy_load_namespace_item_func
        self._get_specified_group_func = get_specified_group_func
        self.lazy_load_namespaces_func = lazy_load_namespaces_func

        self.validate()

    def refresh_key_expire_time(self, key, timestamp=None):
        """刷新过期时间"""
        self._lazy_load_init_ts[key] = int(timestamp or time.time())

    def is_key_expire(self, key):
        if int(time.time()) - self._lazy_load_init_ts.get(key, 0) > self.lazy_load_expire:
            return True

        return False

    def load_lazy_namespaces(self):
        """加载有效的 namespaces"""
        cache_key = "lazy_load_namespaces"
        if self.is_key_expire(cache_key):
            self.lazy_load_namespaces = self.lazy_load_namespaces_func() if self.lazy_load_namespaces_func else []

        self.refresh_key_expire_time(cache_key)

    def validate(self):
        names = set()
        for namespace in self.namespaces_items:
            if namespace.name in names:
                raise ExperimentValidateError("namespace name 冲突")

            names.add(namespace.name)

    def get_namespace_item(self, namespace_name):
        # type: (str) -> NamespaceItem
        if namespace_name in self.namespaces:
            return self.namespaces[namespace_name]

        self.load_lazy_namespaces()
        if namespace_name not in self.lazy_load_namespaces:
            raise ExperimentValidateError("Namespace {} not found.".format(namespace_name))

        if not self.lazy_load_namespace_item_func:
            raise ExperimentValidateError("lazy_load_namespace_item_func not found")

        if namespace_name in self.lazy_load_namespaces and namespace_name in self.lazy_load_namespace_items:
            if self.is_key_expire(namespace_name):
                return self.lazy_load_namespace_items[namespace_name]

        _ns = self.lazy_load_namespace_item_func(namespace_name)
        if not _ns:
            raise ExperimentValidateError("Namespace {} not found".format(namespace_name))

        self.lazy_load_namespace_items[namespace_name] = _ns
        self.refresh_key_expire_time(namespace_name)
        return self.lazy_load_namespace_items[namespace_name]

    def get_tracking_group(self, namespace_name, unit="", user_id=None, pdid=None, track=True, cache=True, **params):
        # type: (str, str, int, str, bool, bool, Dict[Any, Any]) -> Any
        """取分组的全局唯一标识符，带上实验链的信息"""
        try:
            allow_specify_group = experiment_context.allow_specify_group
        except AttributeError:
            allow_specify_group = False
        try:
            cached_group = experiment_context.cached_group
        except AttributeError:
            cached_group = {}

        if unit and allow_specify_group and callable(self._get_specified_group_func):
            group = self._get_specified_group_func(experiment_context, namespace_name, unit, user_id=user_id, pdid=pdid, **params)
            if group:
                _tracking_group = self.get_tracking_group_by_group_name(namespace_name, group)
                if _tracking_group:
                    return _tracking_group

        namespace_item = self.get_namespace_item(namespace_name)

        key = "tracking_group{%s}{%s}" % (namespace_name, unit)

        if cache and key in cached_group:
            return cached_group[key]

        tracking_group = namespace_item.get_group(unit, user_id=user_id, pdid=pdid, **params)
        if not tracking_group:
            return None

        cached_group[key] = tracking_group
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
        tracking_group = self.get_tracking_group(namespace_name, unit, user_id, pdid, track, **params)
        if not tracking_group:
            return None

        return tracking_group.last_group

    def get_tracking_group_by_group_name(self, namespace_name, group_name):
        # type: (str, str) -> Any
        """ 根据实验组名获取tracking_group """
        namespace_item = self.get_namespace_item(namespace_name)  # type: NamespaceItem
        group = namespace_item.get_group_by_name(group_name)
        if group:
            return TrackingGroup(
                group_name=group.name,
                experiment_name="",
                group_extra_params=group.extra_params
            )

    def add_namespace(self, namespace_item):
        # type: (NamespaceItem) -> None
        if namespace_item.name in self.namespaces:
            raise ExperimentValidateError("namespace name 冲突")

        self.namespaces[namespace_item.name] = namespace_item

    def setup_experiment_context(self, user_id=None, device_id=None, origin=None, version=None,
                                 allow_specify_group=False, **kwargs):
        experiment_context.user_id = user_id
        experiment_context.device_id = device_id
        experiment_context.origin = origin
        experiment_context.version = version
        experiment_context.allow_specify_group = allow_specify_group

        experiment_context.cached_group = {}       # 在一次请求生命周期内用于缓存分组结果

        experiment_context.update(kwargs)

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
            yield self.get_group(namespace_name, unit=device_id, pdid=device_id, **params)

        except Exception as e:
            # 这里需要被 fallback 到 control 组
            if self.logger:
                self.logger.error(
                    "auto_group error: namespace_name: {}, msg: {}, params: {}",
                    namespace_name, str(e), simplejson.dumps(params)
                )
            yield None

    @contextmanager
    def auto_tracking_group_by_device_id(self, namespace_name, **params):
        try:
            device_id = experiment_context.device_id
            yield self.get_tracking_group(namespace_name, unit=device_id, pdid=device_id, **params)

        except Exception as e:
            if self.logger:
                self.logger.error(
                    "auto_tracking_group error: namespace_name: {}, msg: {}, params: {}",
                    namespace_name, str(e), simplejson.dumps(params)
                )
            yield None

    @contextmanager
    def auto_tracking_group_by_user_id(self, namespace_name, **params):
        try:
            user_id = experiment_context.user_id

            yield self.get_tracking_group(namespace_name, unit=user_id, user_id=user_id,
                                          **params)
        except Exception as e:
            if self.logger:
                self.logger.error(
                    "auto_tracking_group error: namespace_name: {}, msg: {}, params: {}",
                    namespace_name, str(e), simplejson.dumps(params)
                )
            yield None

    @contextmanager
    def auto_group_by_user_id(self, namespace_name, **params):
        try:
            user_id = experiment_context.user_id
            yield self.get_group(namespace_name, unit=user_id, user_id=user_id,
                                 **params)
        except Exception as e:
            # 这里需要被 fallback 到 control 组
            if self.logger:
                self.logger.error(
                    "auto_group error: namespace_name: {}, msg: {}, params: {}",
                    namespace_name, str(e), simplejson.dumps(params)
                )
            yield None
