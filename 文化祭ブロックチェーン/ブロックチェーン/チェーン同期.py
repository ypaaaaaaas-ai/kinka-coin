# -*- coding: utf-8 -*-
"""
チェーン同期.py
---------------
他ノードとの同期を行うモジュール。

仕様書より:
    「新しいノードがネットワークへ参加した場合、他ノードから現在のチェーン
     情報を取得し、自身のチェーンと比較する。受信したチェーンの長さが
     自身より長い場合、そのチェーンへ切り替える。」
    「同期時はチェーン丸ごと検証」
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "通信"))
import API通信  # noqa: E402

from フォーク管理 import ForkManager  # noqa: E402


class ChainSync:
    """他ノードとのチェーン同期を行うクラス。"""

    def __init__(self, blockchain, node_manager):
        self.blockchain = blockchain
        self.node_manager = node_manager
        self.fork_manager = ForkManager()

    def sync_with_node(self, node_url: str) -> bool:
        """
        指定した1ノードから最新のチェーンを取得し、
        自ノードより長く、かつ検証に成功する場合は切り替える。
        """
        data = API通信.get_json(f"{node_url}/chain")
        if not data or "chain" not in data:
            return False

        candidate_chain = data["chain"]
        return self.blockchain.replace_chain(candidate_chain)

    def sync_with_all_nodes(self) -> bool:
        """
        登録されている全ノードからチェーンを取得し、
        最も長く正しいチェーンをフォーク管理経由で採用する。
        (=新ノード参加時のコンセンサスアルゴリズム)
        """
        candidate_chains = []
        for node in self.node_manager.get_nodes():
            data = API通信.get_json(f"{node}/chain")
            if data and "chain" in data:
                candidate_chains.append(data["chain"])

        if not candidate_chains:
            return False

        resolved = self.fork_manager.resolve(self.blockchain.chain, candidate_chains)
        if resolved != self.blockchain.chain and len(resolved) > len(self.blockchain.chain):
            if self.blockchain.is_chain_valid(resolved):
                self.blockchain.chain = resolved
                return True
        return False
