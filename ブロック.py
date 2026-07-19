# ブロック.py

class Block:
    def __init__(self):
        # ブロック情報を辞書で保持
        self.data = {
            "index": None,           # ブロック番号
            "timestamp": None,       # 取引時間
            "transactions": [],      # 取引情報
            "previous_hash": None,   # 前ブロックのハッシュ値
            "hash": None,            # 自身のハッシュ値
            "nonce": 0               # ナンス
        }

    def get(self, key):
        """
        キーに対応する値を取得
        例: block.get("index")
        """
        return self.data.get(key)

    def write(self, key, value):
        """
        キーに値を書き込む
        例: block.write("index", 1)
        """
        if key in self.data:
            self.data[key] = value
        else:
            raise KeyError(f"存在しないキー: {key}")

    def __str__(self):
        return str(self.data)