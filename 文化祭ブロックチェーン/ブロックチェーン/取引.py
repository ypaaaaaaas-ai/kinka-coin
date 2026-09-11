# -*- coding: utf-8 -*-
"""
取引.py
-------
送金情報(取引)を管理するモジュール。

1件の取引は以下の情報を持つ。
    sender      : 送信者の公開鍵 (採掘報酬の場合は "SYSTEM")
    receiver    : 受信者の公開鍵
    amount      : 送金額
    timestamp   : 取引作成日時
    signature   : 電子署名 (16進文字列。採掘報酬など署名不要な取引はNone)

署名対象データは sender, receiver, amount, timestamp を
連結した文字列とする (電子署名.py の sign()/verify() に渡す)。
"""

import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "暗号"))
import 電子署名  # noqa: E402


class Transaction:
    """1件の送金取引を表すクラス。"""

    def __init__(self, sender, receiver, amount, timestamp=None, signature=None):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.signature = signature

    def _signing_payload(self) -> str:
        """署名/検証の対象となる文字列を作成する。"""
        return f"{self.sender}{self.receiver}{self.amount}{self.timestamp}"

    def sign_transaction(self, private_key):
        """
        秘密鍵で取引データに電子署名を行う。
        採掘報酬(SYSTEM発行)の取引には署名は不要。
        """
        self.signature = 電子署名.sign(self._signing_payload(), private_key)
        return self.signature

    def verify_transaction(self) -> bool:
        """
        公開鍵(=sender)を用いて署名を検証する。
        正しい署名である場合のみTrueを返す(=本人による送金として認証)。
        採掘報酬(senderが"SYSTEM")は署名検証をスキップしTrueを返す。
        """
        if self.sender == "SYSTEM":
            return True
        if not self.signature:
            return False
        return 電子署名.verify(self._signing_payload(), self.signature, self.sender)

    def to_dict(self) -> dict:
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Transaction":
        return cls(
            sender=d.get("sender"),
            receiver=d.get("receiver"),
            amount=d.get("amount"),
            timestamp=d.get("timestamp"),
            signature=d.get("signature"),
        )

    def __repr__(self):
        return f"Transaction({self.sender} -> {self.receiver} : {self.amount})"
