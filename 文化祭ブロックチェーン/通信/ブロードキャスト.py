# -*- coding: utf-8 -*-
"""
ブロードキャスト.py
--------------------
生成した新しいブロックや取引を、登録されている他の全ノードへ送信するモジュール。

仕様書より:
    「新しいブロックはブロードキャストで送られる」
"""

import sys
import os

sys.path.append(os.path.dirname(__file__))
import API通信  # noqa: E402


class Broadcaster:
    """ブロック・取引を他ノードへ一斉送信するクラス。"""

    def __init__(self, node_manager):
        self.node_manager = node_manager

    def broadcast_block(self, block: dict) -> dict:
        """新しいブロックを登録済みの全ノードへ送信する。"""
        results = {}
        for node in self.node_manager.get_nodes():
            url = f"{node}/blocks/receive"
            results[node] = API通信.post_json(url, {"block": block}) is not None
        return results

    def broadcast_transaction(self, transaction: dict) -> dict:
        """新しい取引を登録済みの全ノードへ送信する。"""
        results = {}
        for node in self.node_manager.get_nodes():
            url = f"{node}/transactions/receive"
            results[node] = API通信.post_json(url, {"transaction": transaction}) is not None
        return results
