# -*- coding: utf-8 -*-
"""
残高計算.py
-----------
チェーンから残高を計算するモジュール。

仕様書より:
    「残高はチェーンを先頭から遡って計算する」
=> 口座ごとの残高台帳を持たず、毎回チェーン全体(ジェネシスブロックから
   現在の最新ブロックまで)の取引を積算して残高を求める。
   これにより改ざんが起きた場合も、その時点から残高計算が破綻し、
   不整合を可視化できる。
"""


class BalanceCalculator:
    """チェーンから残高を計算するクラス。"""

    @staticmethod
    def calculate_balance(chain: list, address: str) -> int:
        """
        指定したアドレス(公開鍵)の残高を、
        ジェネシスブロックから現在のチェーン末尾まで走査して計算する。

        Parameters
        ----------
        chain : list[dict]
            ブロック(辞書)のリスト。
        address : str
            残高を計算したいアカウントの公開鍵。

        Returns
        -------
        int
            現在の残高。
        """
        balance = 0
        for block in chain:
            for tx in block.get("transactions", []):
                if tx.get("receiver") == address:
                    balance += tx.get("amount", 0)
                if tx.get("sender") == address:
                    balance -= tx.get("amount", 0)
        return balance

    @staticmethod
    def calculate_all_balances(chain: list) -> dict:
        """チェーンに登場する全アドレスの残高を一括計算して辞書で返す。"""
        balances = {}
        for block in chain:
            for tx in block.get("transactions", []):
                sender = tx.get("sender")
                receiver = tx.get("receiver")
                amount = tx.get("amount", 0)
                if sender and sender != "SYSTEM":
                    balances[sender] = balances.get(sender, 0) - amount
                if receiver:
                    balances[receiver] = balances.get(receiver, 0) + amount
        return balances

    @staticmethod
    def has_sufficient_balance(chain: list, address: str, amount: int) -> bool:
        """送金前チェック: 残高が送金額以上あるかを確認する。"""
        return BalanceCalculator.calculate_balance(chain, address) >= amount
