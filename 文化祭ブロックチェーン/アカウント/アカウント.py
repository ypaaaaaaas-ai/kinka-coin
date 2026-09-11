# -*- coding: utf-8 -*-
"""
アカウント.py
-------------
ユーザー情報(ユーザー名 + 財布)を管理するクラス。
新規アカウント作成時に 財布.py で鍵ペアを生成し、
データベース/アカウント保存.py を通じて永続化する。
"""

import sys
import os

sys.path.append(os.path.dirname(__file__))
from 財布 import Wallet  # noqa: E402


class Account:
    """1ユーザー分のアカウント情報を管理するクラス。"""

    def __init__(self, username: str, wallet: Wallet = None):
        self.username = username
        self.wallet = wallet or Wallet()

    @classmethod
    def create_new(cls, username: str) -> "Account":
        """新規アカウントを作成する。鍵ペアもここで生成される。"""
        wallet = Wallet()
        wallet.generate()
        return cls(username=username, wallet=wallet)

    @classmethod
    def from_keys(cls, username: str, public_key: str, private_key: str) -> "Account":
        """既存の鍵情報からアカウントを復元する(DBからのロード用)。"""
        wallet = Wallet()
        account = cls(username=username, wallet=wallet)
        account._restore_keys(public_key, private_key)
        return account

    def _restore_keys(self, public_key: str, private_key: str):
        """DBから読み込んだPEM鍵文字列を財布に直接セットする。"""
        from Crypto.PublicKey import RSA
        key = RSA.import_key(private_key)
        self.wallet._key_manager._private_key = key
        self.wallet._key_manager._public_key = RSA.import_key(public_key)
        self.wallet._generated = True

    def get_public_key(self):
        return self.wallet.get_public_key()

    def get_private_key(self):
        return self.wallet.get_private_key()

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "public_key": self.get_public_key(),
        }

    def __repr__(self):
        return f"Account(username={self.username})"
