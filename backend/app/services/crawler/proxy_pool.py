"""IP 代理池：轮询获取、故障标记与剔除"""
import random
import threading


class ProxyPool:
    """轻量代理池，支持从配置加载、随机/轮询选择、故障剔除"""

    def __init__(self, proxies=None):
        self._proxies = {}   # proxy -> fail_count
        self._lock = threading.Lock()
        for p in (proxies or []):
            p = p.strip()
            if p:
                self._proxies[p] = 0

    @property
    def size(self) -> int:
        return len(self._proxies)

    def is_empty(self) -> bool:
        return len(self._proxies) == 0

    def get(self):
        """获取一个代理（轮询）"""
        with self._lock:
            if not self._proxies:
                return None
            candidates = list(self._proxies.keys())
            return random.choice(candidates)

    def mark_fail(self, proxy):
        """标记代理失败，连续失败超过阈值则剔除"""
        with self._lock:
            if proxy not in self._proxies:
                return
            self._proxies[proxy] += 1
            if self._proxies[proxy] >= 3:
                del self._proxies[proxy]

    def mark_success(self, proxy):
        with self._lock:
            if proxy in self._proxies:
                self._proxies[proxy] = 0

    def to_list(self):
        with self._lock:
            return list(self._proxies.keys())
