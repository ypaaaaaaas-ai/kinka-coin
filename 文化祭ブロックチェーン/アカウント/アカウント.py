# -*- coding: utf-8 -*-
"""
アカウント.py
-------------
ユーザー情報(ユーザー名 + パスワード + 財布)を管理するクラス。
新規アカウント作成時に 財布.py で鍵ペアを生成し、パスワードは
暗号/パスワード.py でPBKDF2ハッシュ化してから、
データベース/アカウント保存.py を通じて永続化する。
"""

import sys
import os

sys.path.append(os.path.dirname(__file__))
from 財布 import Wallet  # noqa: E402

# 暗号パッケージ(パスワード.py)をimportできるようにパスを追加
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "暗号"))
from パスワード import hash_password  # noqa: E402


class Account:
    """1ユーザー分のアカウント情報(名前・パスワードハッシュ・財布)を管理するクラス。"""

    def __init__(self, username: str, wallet: Wallet = None,
                 password_hash: str = None, salt: str = None):
        self.username = username
        self.wallet = wallet or Wallet()
        self.password_hash = password_hash
        self.salt = salt

    @classmethod
    def create_new(cls, username: str, password: str) -> "Account":
        """
        新規アカウントを作成する。鍵ペアの生成と、パスワードのPBKDF2ハッシュ化
        (ランダムsalt付き)はここで行う。平文パスワードはこの場限りで捨て、
        ハッシュとsaltだけを後段(DB保存)へ渡す。
        """
        wallet = Wallet()
        wallet.generate()
        password_hash, salt = hash_password(password)
        return cls(username=username, wallet=wallet,
                   password_hash=password_hash, salt=salt)

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

    def get_password_hash(self):
        return self.password_hash

    def get_salt(self):
        return self.salt

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "public_key": self.get_public_key(),
        }

    def __repr__(self):
        return f"Account(username={self.username})"
