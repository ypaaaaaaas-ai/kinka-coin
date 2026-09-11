# -*- coding: utf-8 -*-
"""
鍵管理.py
---------
公開鍵と秘密鍵を生成・保持するモジュール。
PyCryptodome (Crypto.PublicKey.RSA) を使用する。

このファイルは「鍵の生成と保持」のみを担当し、
署名の生成・検証は 電子署名.py が担当する。
"""

from Crypto.PublicKey import RSA


class KeyManager:
    """RSA公開鍵・秘密鍵を生成し、内部で保持するクラス。"""

    def __init__(self, key_size: int = 2048):
        self._key_size = key_size
        self._private_key = None
        self._public_key = None

    def generate(self):
        """
        RSA公開鍵・秘密鍵のペアを新規に生成し、内部に保持する。
        生成後は get_public_key() / get_private_key() で取得できる。
        """
        key = RSA.generate(self._key_size)
        self._private_key = key
        self._public_key = key.publickey()
        return self

    def get_public_key(self):
        """
        保持している公開鍵を返す (PEM形式の文字列)。
        まだ generate() されていない場合は None を返す。
        """
        if self._public_key is None:
            return None
        return self._public_key.export_key().decode("utf-8")

    def get_private_key(self):
        """
        保持している秘密鍵を返す (PEM形式の文字列)。
        まだ generate() されていない場合は None を返す。
        """
        if self._private_key is None:
            return None
        return self._private_key.export_key().decode("utf-8")


if __name__ == "__main__":
    km = KeyManager()
    km.generate()
    print("公開鍵:")
    print(km.get_public_key())
    print("秘密鍵:")
    print(km.get_private_key())
