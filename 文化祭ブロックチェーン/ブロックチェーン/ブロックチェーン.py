# -*- coding: utf-8 -*-
"""
ブロックチェーン.py
-------------------
ブロックチェーン全体(チェーン + 未承認取引)を管理するクラス。

役割:
    - ジェネシスブロックの生成
    - 未承認取引の追加(追加前に必ず検証)
    - 新しいブロックの追加(追加前に必ず検証)
    - 残高計算・チェーン検証への橋渡し
"""

import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "暗号"))
import ハッシュ  # noqa: E402

from ブロック import Block  # noqa: E402
from 検証器 import Validator  # noqa: E402
from 残高計算 import BalanceCalculator  # noqa: E402


class Blockchain:
    """1ノードが保持するブロックチェーン全体を管理するクラス。"""

    def __init__(self):
        self.chain: list = []
        self.pending_transactions: list = []
        self.validator = Validator()
        self._create_genesis_block()

    # ---------------- 初期化 ----------------

    def _create_genesis_block(self):
        """チェーンの先頭ブロック(ジェネシスブロック)を作成する。"""
        genesis = Block(
            index=0,
            timestamp=datetime.now(timezone.utc).isoformat(),
            transactions=[],
            previous_hash="0" * 64,
            nonce=0,
        )
        block_dict = genesis.to_dict()
        block_dict["hash"] = ハッシュ.calculate(block_dict)
        self.chain.append(block_dict)

    # ---------------- 参照系 ----------------

    def get_latest_block(self) -> dict:
        """チェーン末尾(最新)のブロックを返す。"""
        return self.chain[-1]

    def get_length(self) -> int:
        return len(self.chain)

    def get_balance(self, address: str) -> int:
        return BalanceCalculator.calculate_balance(self.chain, address)

    # ---------------- 取引の追加 ----------------

    def add_transaction(self, transaction: dict) -> bool:
        """
        未承認取引として一時保存する。
        「受信時は必ず検証」に基づき、追加前に署名・残高を検証する。
        """
        if not self.validator.validate_transaction(transaction):
            return False

        # 残高チェック(採掘報酬のSYSTEM送金は対象外)
        if transaction.get("sender") != "SYSTEM":
            if not BalanceCalculator.has_sufficient_balance(
                self.chain, transaction.get("sender"), transaction.get("amount", 0)
            ):
                return False

        self.pending_transactions.append(transaction)
        return True

    # ---------------- ブロックの追加 ----------------

    def add_block(self, block: dict) -> bool:
        """
        新しいブロックをチェーンに追加する。
        「追加前も必ず検証」に基づき、追加前に整合性を検証する。
        """
        previous_block = self.get_latest_block()
        if not self.validator.validate_block(block, previous_block):
            return False

        self.chain.append(block)

        # ブロックに取り込まれた取引をpendingから取り除く
        included = {
            (tx.get("sender"), tx.get("receiver"), tx.get("amount"), tx.get("timestamp"))
            for tx in block.get("transactions", [])
        }
        self.pending_transactions = [
            tx for tx in self.pending_transactions
            if (tx.get("sender"), tx.get("receiver"), tx.get("amount"), tx.get("timestamp"))
            not in included
        ]
        return True

    # ---------------- チェーン全体の検証・置換 ----------------

    def is_chain_valid(self, chain: list = None) -> bool:
        """「同期時はチェーン丸ごと検証」に基づき、チェーン全体を検証する。"""
        target = chain if chain is not None else self.chain
        return self.validator.validate_chain(target)

    def replace_chain(self, new_chain: list) -> bool:
        """
        より長い正しいチェーンを受け取った場合に、自身のチェーンを置き換える。
        最長チェームルールの実体はここ(と フォーク管理.py)。
        """
        if len(new_chain) <= len(self.chain):
            return False
        if not self.is_chain_valid(new_chain):
            return False
        self.chain = new_chain
        return True

    def to_list(self) -> list:
        return list(self.chain)
