# -*- coding: utf-8 -*-
"""
ブロック.py
-----------
ブロックチェーンを構成する「ブロック」1個を表現するクラス。

保持する項目 (キー):
    index         : ブロック番号 (int)
    timestamp     : 取引時間 (str)
    transactions  : 取引一覧 (list[dict])
    previous_hash : 前ブロックのハッシュ値 (str)
    hash          : 自身のハッシュ値 (str)
    nonce         : 採掘(Proof of Work)に使う値 (int)

インスタンス名.get(key名) で値を取得し、
インスタンス名.write(key名, value) で値を書き込める。
"""


class Block:
    """ブロック1個を表現するクラス。"""

    _KEYS = ("index", "timestamp", "transactions", "previous_hash", "hash", "nonce")

    def __init__(self, index=None, timestamp=None, transactions=None,
                 previous_hash=None, hash=None, nonce=0):
        self._data = {
            "index": index,
            "timestamp": timestamp,
            "transactions": transactions if transactions is not None else [],
            "previous_hash": previous_hash,
            "hash": hash,
            "nonce": nonce,
        }

    def get(self, key名):
        """指定したキーの値を取得する。存在しないキーはNoneを返す。"""
        return self._data.get(key名)

    def write(self, key名, value名):
        """指定したキーに値を書き込む(上書きする)。"""
        if key名 not in self._KEYS:
            raise KeyError(f"不正なキーです: {key名}")
        self._data[key名] = value名
        return self

    def to_dict(self) -> dict:
        """内部辞書のコピーを返す(ハッシュ計算やDB保存・JSON化に使う)。"""
        return dict(self._data)

    @classmethod
    def from_dict(cls, d: dict) -> "Block":
        """辞書からBlockインスタンスを復元する。"""
        return cls(
            index=d.get("index"),
            timestamp=d.get("timestamp"),
            transactions=d.get("transactions", []),
            previous_hash=d.get("previous_hash"),
            hash=d.get("hash"),
            nonce=d.get("nonce", 0),
        )

    def __repr__(self):
        return f"Block(index={self.get('index')}, hash={self.get('hash')})"


if __name__ == "__main__":
    b = Block(index=0, timestamp="2026-08-18T00:00:00", transactions=[],
               previous_hash="0" * 64, nonce=0)
    b.write("hash", "abc123")
    print(b.get("index"), b.get("hash"))
    print(b.to_dict())
