# -*- coding: utf-8 -*-
"""
フォーク管理.py
---------------
ノード間で異なるブロックが同時に生成された場合に発生する
「フォーク(分岐)」を管理するモジュール。

方針(仕様書より):
    - 最も長いチェーンを正統チェーンとして採用する。
    - 短いチェーンは孤立ブロック(orphan)として保持する
      (削除はせず、展示用に「なぜ採用されなかったか」を見せられるようにする)。
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "暗号"))
from 検証器 import Validator  # noqa: E402


class ForkManager:
    """分岐したチェーンを管理するクラス。"""

    def __init__(self):
        # 採用されなかった孤立ブロック/チェーンを保持しておく(展示用)
        self.orphan_chains: list = []

    def resolve(self, main_chain: list, candidate_chains: list) -> list:
        """
        現在の正統チェーン(main_chain)と、他ノードなどから届いた
        候補チェーン群(candidate_chains)を比較し、
        最も長い「正しい」チェーンを正統チェーンとして返す。

        採用されなかったチェーンは孤立チェーンとして保持する。

        Parameters
        ----------
        main_chain : list[dict]
            現在自ノードが持つチェーン。
        candidate_chains : list[list[dict]]
            比較対象となる他のチェーン(複数)。

        Returns
        -------
        list[dict]
            採用すべき正統チェーン。
        """
        best_chain = main_chain
        best_length = len(main_chain)

        for candidate in candidate_chains:
            if not Validator.validate_chain(candidate):
                # 不正なチェーンは無視(孤立扱いにもしない)
                continue

            if len(candidate) > best_length:
                # これまでのベストは孤立チェーンとして退避
                if best_chain is not main_chain or best_chain != candidate:
                    self.orphan_chains.append(best_chain)
                best_chain = candidate
                best_length = len(candidate)
            else:
                # 採用されなかった候補は孤立チェーンとして保持
                self.orphan_chains.append(candidate)

        return best_chain

    def get_orphans(self) -> list:
        """展示用: これまでに採用されなかった孤立チェーンの一覧を返す。"""
        return list(self.orphan_chains)

    def detect_fork_point(self, chain_a: list, chain_b: list) -> int:
        """2つのチェーンが分岐したブロック番号(index)を返す(展示表示用)。"""
        fork_index = 0
        for i in range(min(len(chain_a), len(chain_b))):
            if chain_a[i].get("hash") != chain_b[i].get("hash"):
                return i
            fork_index = i
        return fork_index
