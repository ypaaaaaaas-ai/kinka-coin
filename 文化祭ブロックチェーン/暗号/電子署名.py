# -*- coding: utf-8 -*-
"""
電子署名.py
-----------
電子署名の生成(sign)と検証(verify)を行うモジュール。

鍵の生成・保持は 鍵管理.py (KeyManager) が担当する。
このファイルでは鍵の生成を行わず、
鍵管理.py の get_private_key() / get_public_key() で取得した
PEM形式の鍵文字列を受け取って署名処理のみを行う。

RSA-PSS方式 + SHA-256 を使用する (PyCryptodome)。
"""

from Crypto.PublicKey import RSA
from Crypto.Signature import pss
from Crypto.Hash import SHA256


def _to_bytes(data) -> bytes:
    """文字列ならUTF-8でバイト列に変換する。既にbytesならそのまま返す。"""
    if isinstance(data, bytes):
        return data
    return str(data).encode("utf-8")


def sign(data, private_key) -> str:
    """
    データに対してRSA-PSS方式で電子署名を生成する。

    Parameters
    ----------
    data : str | bytes
        署名対象のデータ。
    private_key : str | bytes
        鍵管理.py の get_private_key() で取得したPEM形式の秘密鍵。

    Returns
    -------
    str
        生成した署名を16進文字列に変換した値。
    """
    key = RSA.import_key(private_key)
    data_bytes = _to_bytes(data)
    h = SHA256.new(data_bytes)
    signature_bytes = pss.new(key).sign(h)
    return signature_bytes.hex()


def verify(data, signature: str, public_key) -> bool:
    """
    電子署名を検証する。

    Parameters
    ----------
    data : str | bytes
        署名対象だったデータ (sign()に渡したものと同じ内容)。
    signature : str
        sign() が返した16進文字列の署名。
    public_key : str | bytes
        鍵管理.py の get_public_key() で取得したPEM形式の公開鍵。

    Returns
    -------
    bool
        署名が正しい場合はTrue、正しくない場合(データ改ざん・不正な鍵など)はFalse。
    """
    try:
        key = RSA.import_key(public_key)
        data_bytes = _to_bytes(data)
        h = SHA256.new(data_bytes)
        signature_bytes = bytes.fromhex(signature)
        pss.new(key).verify(h, signature_bytes)
        return True
    except (ValueError, TypeError):
        # 署名不一致、鍵不正、16進変換失敗などは全て「検証失敗」として扱う
        return False


if __name__ == "__main__":
    from 鍵管理 import KeyManager

    km = KeyManager()
    km.generate()

    message = "田中 -> 鈴木 : 10コイン"
    sig = sign(message, km.get_private_key())
    print("署名:", sig)
    print("正しいデータでの検証:", verify(message, sig, km.get_public_key()))
    print("改ざんデータでの検証:", verify(message + "改ざん", sig, km.get_public_key()))
