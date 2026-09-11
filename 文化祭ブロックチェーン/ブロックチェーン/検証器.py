# -*- coding: utf-8 -*-
"""
検証器.py
---------
取引・ブロック・チェーン全体の正当性を確認するモジュール。

方針(仕様書より):
    「受信時は必ず検証」
    「追加前も必ず検証」
    「同期時はチェーン丸ごと検証」
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "暗号"))
import ハッシュ  # noqa: E402

from 取引 import Transaction  # noqa: E402


class Validator:
    """取引・ブロック・チェーンの検証を行うクラス。"""

    # ---------------- 取引の検証 ----------------

    @staticmethod
    def validate_transaction(transaction) -> bool:
        """
        1件の取引が正当かどうかを検証する。
        - 電子署名が正しいこと(本人による送金であること)
        - 送金額が0より大きいこと
        """
        if isinstance(transaction, dict):
            transaction = Transaction.from_dict(transaction)

        if transaction.amount is None or transaction.amount <= 0:
            return False
        if transaction.sender == transaction.receiver:
            return False
        return transaction.verify_transaction()

    # ---------------- ブロックの検証 ----------------

    @staticmethod
    def validate_block(block: dict, previous_block: dict) -> bool:
        """
        1個のブロックが正当かどうかを検証する。

        - ブロック番号が前ブロック+1であること
        - previous_hash が前ブロックの hash と一致すること
        - ブロックの内容から再計算したハッシュ値が
          ブロックが保持する hash と一致すること (改ざん検知)
        """
        if block.get("index") != previous_block.get("index") + 1:
            return False

        if block.get("previous_hash") != previous_block.get("hash"):
            return False

        recalculated = ハッシュ.calculate(block)
        if recalculated != block.get("hash"):
            return False

        return True

    @staticmethod
    def validate_genesis_block(block: dict) -> bool:
        """先頭(ジェネシス)ブロックの整合性のみを確認する。"""
        recalculated = ハッシュ.calculate(block)
        return recalculated == block.get("hash")

    # ---------------- チェーン全体の検証 ----------------

    @classmethod
    def validate_chain(cls, chain: list) -> bool:
        """
        チェーン全体(ブロックの辞書のリスト)を先頭から検証する。
        1つでも不整合があれば改ざんとみなし False を返す。
        """
        if not chain:
            return False

        if not cls.validate_genesis_block(chain[0]):
            return False

        for i in range(1, len(chain)):
            if not cls.validate_block(chain[i], chain[i - 1]):
                return False

        return True
