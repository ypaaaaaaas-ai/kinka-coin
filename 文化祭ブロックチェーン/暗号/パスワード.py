# -*- coding: utf-8 -*-
"""
パスワード.py
-------------
ユーザー名+パスワードでのログインのためのパスワード管理モジュール。

設計方針:
- パスワードは平文のままDBに保存しない。PBKDF2-HMAC-SHA256でハッシュ化して
  保存する(ハッシュ関数の教科書的な「一方向性」の実践例でもある)。
- salt(塩)はアカウントごとにランダム生成し、同じパスワードでも別のハッシュに
  なるようにする(レインボーテーブル対策の基本)。
- hashlib / secrets はPython標準ライブラリなので、追加パッケージは不要。
- 本格的な認証基盤ではないが、教育用途として「パスワードはハッシュで保存する」
  という現代の常識的な作法を実装として体験できる構成にしている。
"""

import hashlib
import secrets

# PBKDF2のストレッチ回数。
# 大きいほど総当たり攻撃に強いが、ログイン時の計算時間が伸びる。
# 展示運用での体感速度と安全性のバランスを取り、10万回としている。
PBKDF2_ITERATIONS = 100_000

# saltの長さ(バイト数)。16バイト=32文字の16進数文字列になる。
SALT_BYTES = 16


def generate_salt() -> str:
    """アカウントごとのsalt(16進数文字列)を暗号学的に安全な乱数で生成する。"""
    return secrets.token_hex(SALT_BYTES)


def hash_password(password: str, salt: str = None) -> tuple:
    """
    パスワードをPBKDF2-HMAC-SHA256でハッシュ化する。

    引数:
        password: 平文パスワード
        salt:     16進数文字列のsalt。Noneなら新規にランダム生成する
                  (検証時はDBに保存済みのsaltを渡す)。

    戻り値:
        (password_hash, salt) のタプル。どちらも文字列。
    """
    if salt is None:
        salt = generate_salt()
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PBKDF2_ITERATIONS,
    )
    return digest.hex(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """
    入力されたパスワードが、DBに保存済みのハッシュと一致するかを検証する。

    引数:
        password:      ユーザーが入力した平文パスワード
        password_hash: DBに保存されているハッシュ値(16進数文字列)
        salt:          DBに保存されているsalt(16進数文字列)

    戻り値:
        一致すればTrue、一致しなければFalse。
        (過去のアカウントでパスワードが未設定のものはFalseになる)
    """
    if not password_hash or not salt:
        return False
    computed, _ = hash_password(password, salt)
    # 単純な == 比較ではなく定数時間比較を使い、タイミング攻撃の余地を減らす
    return secrets.compare_digest(computed, password_hash)


if __name__ == "__main__":
    # 動作確認用のミニテスト: python パスワード.py
    h1, s1 = hash_password("tanaka1234")
    h2, s2 = hash_password("tanaka1234")
    print("同一パスワードでもsaltが違えばハッシュも違う:", h1 != h2)
    print("正しいパスワードの検証:", verify_password("tanaka1234", h1, s1))
    print("誤ったパスワードの検証:", verify_password("wrongpass", h1, s1))
    print("ハッシュ例:", h1[:32], "... / salt:", s1)
