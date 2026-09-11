# -*- coding: utf-8 -*-
"""
ノード管理.py
-------------
接続中の他ノード(URL)一覧を管理するモジュール。
"""

from urllib.parse import urlparse


class NodeManager:
    """ネットワークに参加している他ノードのURLを管理するクラス。"""

    def __init__(self):
        self.nodes: set = set()

    def register_node(self, address: str) -> bool:
        """
        ノードのURL(例: http://192.168.1.10:5001)を登録する。

        Returns
        -------
        bool
            登録に成功した場合True、URLが不正な場合False。
        """
        parsed = urlparse(address)
        if not parsed.netloc and not parsed.path:
            return False

        # http(s):// が省略された場合を補完
        if parsed.netloc:
            self.nodes.add(f"{parsed.scheme}://{parsed.netloc}")
        else:
            self.nodes.add(f"http://{parsed.path}")
        return True

    def remove_node(self, address: str):
        self.nodes.discard(address)

    def get_nodes(self) -> list:
        return list(self.nodes)

    def clear(self):
        self.nodes.clear()
