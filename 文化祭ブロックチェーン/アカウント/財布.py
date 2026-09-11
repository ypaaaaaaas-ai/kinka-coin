# -*- coding: utf-8 -*-
"""
財布.py
-------
公開鍵と秘密鍵を保持するクラス。
鍵の生成そのものは 暗号/鍵管理.py (KeyManager) に委譲する。
"""

import sys
import os

# 暗号パッケージをimportできるようにパスを追加
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "暗号"))

from 鍵管理 import KeyManager  # noqa: E402


class Wallet:
    """公開鍵・秘密鍵を保持するクラス。"""

    def __init__(self):
        self._key_manager = KeyManager()
        self._generated = False

    def generate(self):
        """鍵管理.py を利用して公開鍵・秘密鍵を生成し、内部で保持する。"""
        self._key_manager.generate()
        self._generated = True
        return self

    def get_public_key(self):
        """保持している公開鍵を返す。"""
        return self._key_manager.get_public_key()

    def get_private_key(self):
        """保持している秘密鍵を返す。"""
        return self._key_manager.get_private_key()

    def is_generated(self) -> bool:
        return self._generated


if __name__ == "__main__":
    w = Wallet()
    w.generate()
    print("公開鍵:", w.get_public_key()[:60], "...")
    print("秘密鍵:", w.get_private_key()[:60], "...")
