# coding: utf-8

import threading
from multiprocessing import Pool

import gevent

from outplan.local import Local, greenlet_ident


class ThreadUnit(threading.Thread):
    def __init__(self, local, n):
        self.local = local
        self.n = n
        threading.Thread.__init__(self)

    def run(self):
        self.local.a = self.n


local = Local()


def modify_local(n):
    local.a = n
    return local.a


def get_ident(*args):
    return greenlet_ident()


def test_local():
    local.a = 10
    assert local.a == 10

    pool = Pool(8)

    # fork-safe
    res = pool.map(modify_local, list(range(5)))
    assert res == list(range(5))
    assert local.a == 10

    # thread-local(greenlet-local)
    threads = []
    for i in range(5):
        thread = ThreadUnit(local, i)
        threads.append(thread)
        thread.start()

    for t in threads:
        t.join()

    assert local.a == 10

    # greenlet-local
    spawns = []
    for i in range(5):
        spawns.append(gevent.spawn(modify_local, i))

    gevent.joinall(spawns)

    for idx, spawn in enumerate(spawns):
        assert spawn.value == idx

    assert local.a == 10


def test_get_greenlet_ident():
    ids = []

    def worker():
        ids.append(greenlet_ident())
    gs = []
    N_THREADS = 5
    for _ in range(N_THREADS):
        gs.append(gevent.spawn(worker))
    gevent.joinall(gs)

    assert len(set(ids)) == N_THREADS
