from os import getpid

try:
    from greenlet import getcurrent as get_ident
except ImportError:
    try:
        from thread import get_ident
    except ImportError:
        from _thread import get_ident


def greenlet_ident():
    ident = get_ident()
    try:
        ident = int(ident)
    except TypeError:
        # greenlet.getcurrent() return greenlet.greenlet object.
        ident = id(ident)

    idents = [ident, int(getpid())]
    return "-".join(str(i) for i in idents)


class Local:
    """A fork-safe Greenlet-local object.

    Example:

        >>> l = Local()
        >>> l.a = 10
        >>> assert l.a == 10
        >>> l.release()
        >>> assert not hasattr(l, "a")

        >>> l = Local()
        >>> l.a = 1
        >>> import gevent
        >>> f = lambda: l.release()
        >>> gevent.spawn(f).join()
        >>> assert l.a = 1

    """

    __slots__ = ("__storage__", "__ident_func__")

    def __init__(self):
        object.__setattr__(self, "__storage__", {})
        object.__setattr__(self, "__ident_func__", greenlet_ident)

    def __iter__(self):
        return iter(self.__storage__.items())

    def __getattr__(self, name):
        try:
            return self.__storage__[self.__ident_func__()][name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        ident = self.__ident_func__()
        storage = self.__storage__
        try:
            storage[ident][name] = value
        except KeyError:
            storage[ident] = {name: value}

    def __delattr__(self, name):
        try:
            del self.__storage__[self.__ident_func__()][name]
        except KeyError:
            raise AttributeError(name)

    def update(self, items):
        self.__storage__[self.__ident_func__()].update(items)

    def release(self):
        self.__storage__.pop(self.__ident_func__(), None)


experiment_context = Local()
