# 電子署名.py
# 電子署名の生成と検証を行う
# RSA-PSS + SHA-256 を使用する

from Crypto.Hash import SHA256
from Crypto.Signature import pss


def _to_bytes(data):
    """署名対象のデータをバイト列へ変換する。"""
    if isinstance(data, str):
        return data.encode("utf-8")

    if isinstance(data, bytes):
        return data

    raise TypeError("dataはstrまたはbytesである必要があります")


def sign(data, private_key):
    """
    RSA秘密鍵を使用して電子署名を生成する。

    Args:
        data: 署名対象のデータ（strまたはbytes）
        private_key: 鍵管理.pyから取得したRSA秘密鍵

    Returns:
        電子署名を16進文字列で返す。
    """
    data = _to_bytes(data)

    # SHA-256でハッシュを計算
    hash_value = SHA256.new(data)

    # RSA-PSSで署名
    signer = pss.new(private_key)
    signature = signer.sign(hash_value)

    # 保存・通信しやすい16進文字列へ変換
    return signature.hex()


def verify(data, signature, public_key):
    """
    RSA公開鍵を使用して電子署名を検証する。

    Args:
        data: 署名対象のデータ（strまたはbytes）
        signature: sign()で生成した16進文字列
        public_key: 鍵管理.pyから取得したRSA公開鍵

    Returns:
        署名が正しければTrue、正しくなければFalse。
    """
    data = _to_bytes(data)

    try:
        # 16進文字列をバイト列へ戻す
        signature_bytes = bytes.fromhex(signature)

        # sign()と同じSHA-256を使用
        hash_value = SHA256.new(data)

        # RSA-PSSで検証
        verifier = pss.new(public_key)
        verifier.verify(hash_value, signature_bytes)

        return True

    except (ValueError, TypeError):
        # 改ざん・不正な署名・不正な形式など
        return False
