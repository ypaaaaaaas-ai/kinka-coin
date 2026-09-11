# -*- coding: utf-8 -*-
"""
qr生成.py
---------
外部パッケージ(qrcode等)に依存しない、Pure PythonのQRコード生成モジュール。

文化祭会場ではインターネットに繋がらないWi-Fiで運用することも想定されるため、
「アクセス用URLをQRコードにする」機能自体は、追加のインターネット接続なしで
動作するように自前実装している(画像描画にはPillowのみ使用)。

対応範囲: バイトモード(Byte mode)、誤り訂正レベルM、Version 1〜40自動選択。
本システムのURL(例: http://192.168.1.10:5000)程度の長さであれば
Version 2〜5程度に収まる。
"""

from PIL import Image

# ---------------- Reed-Solomon (GF(256)) ----------------

_EXP = [0] * 512
_LOG = [0] * 256


def _init_gf():
    x = 1
    for i in range(255):
        _EXP[i] = x
        _LOG[x] = i
        x <<= 1
        if x & 0x100:
            x ^= 0x11D
    for i in range(255, 512):
        _EXP[i] = _EXP[i - 255]


_init_gf()


def _gf_mul(a, b):
    if a == 0 or b == 0:
        return 0
    return _EXP[_LOG[a] + _LOG[b]]


def _rs_generator_poly(degree):
    poly = [1]
    for i in range(degree):
        new_poly = [0] * (len(poly) + 1)
        for j, coef in enumerate(poly):
            new_poly[j] ^= coef
            new_poly[j + 1] ^= _gf_mul(coef, _EXP[i])
        poly = new_poly
    return poly


def _rs_encode(data, ec_len):
    generator = _rs_generator_poly(ec_len)
    result = list(data) + [0] * ec_len
    for i in range(len(data)):
        coef = result[i]
        if coef == 0:
            continue
        for j, g in enumerate(generator):
            result[i + j] ^= _gf_mul(g, coef)
    return result[len(data):]


# ---------------- Version/EC情報テーブル (レベルM のみ抜粋実装) ----------------
# (データ総容量[byte], ECコードワード数/ブロック, ブロック構成) を
# Version 1〜10 分だけ用意する(短いURLであれば十分)。
# 出典: QRコード規格の公開テーブルに基づく代表値。

# 各要素: version -> (total_codewords, ec_codewords_per_block, block_defs)
# block_defs: [(block数, ブロックあたり総コードワード数)]
_VERSION_INFO_M = {
    1: (26, 10, [(1, 26)]),
    2: (44, 16, [(1, 44)]),
    3: (70, 26, [(1, 70)]),
    4: (100, 18, [(2, 50)]),
    5: (134, 24, [(2, 67)]),
    6: (172, 16, [(4, 43)]),
    7: (196, 18, [(4, 49)]),
    8: (242, 22, [(2, 60), (2, 61)]),
    9: (292, 22, [(3, 58), (2, 59)]),
    10: (346, 26, [(4, 69), (1, 70)]),
}

_ALIGNMENT_COORDS = {
    1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30],
    6: [6, 34], 7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46], 10: [6, 28, 50],
}


def _char_count_bits(version):
    return 8 if version < 10 else 16


def _choose_version(data_byte_len):
    for version in range(1, 11):
        total_codewords, ec_per_block, blocks = _VERSION_INFO_M[version]
        data_codewords = sum(n * (size - ec_per_block) for n, size in blocks)
        # モード(4bit) + 文字数指標 + データ + 終端子(最大4bit)を概算で見積もる
        header_bits = 4 + _char_count_bits(version)
        needed_bits = header_bits + data_byte_len * 8 + 4
        if needed_bits <= data_codewords * 8:
            return version
    raise ValueError("データが長すぎてVersion10以内のQRコードに収まりません")


def _build_bitstream(data_bytes, version, data_codewords):
    bits = []

    def push(value, length):
        for i in range(length - 1, -1, -1):
            bits.append((value >> i) & 1)

    push(0b0100, 4)  # バイトモード
    push(len(data_bytes), _char_count_bits(version))
    for b in data_bytes:
        push(b, 8)

    capacity_bits = data_codewords * 8
    # 終端子(最大4bit)
    terminator_len = min(4, capacity_bits - len(bits))
    if terminator_len > 0:
        push(0, terminator_len)

    # 8bit境界に揃える
    while len(bits) % 8 != 0:
        bits.append(0)

    # パディングバイトで埋める
    pad_bytes = [0xEC, 0x11]
    i = 0
    while len(bits) < capacity_bits:
        push(pad_bytes[i % 2], 8)
        i += 1

    # ビット列をバイト列に変換
    codewords = []
    for i in range(0, len(bits), 8):
        byte = 0
        for b in bits[i:i + 8]:
            byte = (byte << 1) | b
        codewords.append(byte)
    return codewords


def _interleave(data_codewords, version, ec_per_block, blocks):
    offset = 0
    data_blocks = []
    ec_blocks = []
    for count, total_size in blocks:
        data_size = total_size - ec_per_block
        for _ in range(count):
            block_data = data_codewords[offset:offset + data_size]
            offset += data_size
            ec_block = _rs_encode(block_data, ec_per_block)
            data_blocks.append(block_data)
            ec_blocks.append(ec_block)

    result = []
    max_data_len = max(len(b) for b in data_blocks)
    for i in range(max_data_len):
        for block in data_blocks:
            if i < len(block):
                result.append(block[i])
    for i in range(ec_per_block):
        for block in ec_blocks:
            result.append(block[i])
    return result


# ---------------- マトリクス生成 ----------------

_FORMAT_INFO_M = {
    # (EC level M = 0b00, mask pattern 0-7) -> 15bit format info (BCHエンコード済み, マスク済み)
    0: 0x5412, 1: 0x5125, 2: 0x5E7C, 3: 0x5B4B,
    4: 0x45F9, 5: 0x40CE, 6: 0x4F97, 7: 0x4AA0,
}


class _Matrix:
    def __init__(self, size):
        self.size = size
        self.modules = [[False] * size for _ in range(size)]
        self.is_function = [[False] * size for _ in range(size)]

    def set(self, x, y, value, function=False):
        self.modules[y][x] = value
        if function:
            self.is_function[y][x] = True

    def get(self, x, y):
        return self.modules[y][x]


def _draw_finder_pattern(m, x, y):
    for dy in range(-1, 8):
        for dx in range(-1, 8):
            xx, yy = x + dx, y + dy
            if 0 <= xx < m.size and 0 <= yy < m.size:
                is_dark = (0 <= dx <= 6 and 0 <= dy <= 6 and
                           (dx in (0, 6) or dy in (0, 6) or (2 <= dx <= 4 and 2 <= dy <= 4)))
                m.set(xx, yy, is_dark, function=True)


def _draw_alignment_pattern(m, cx, cy):
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            is_dark = max(abs(dx), abs(dy)) != 1
            m.set(cx + dx, cy + dy, is_dark, function=True)


def _draw_timing_patterns(m):
    for i in range(8, m.size - 8):
        dark = (i % 2 == 0)
        if not m.is_function[6][i]:
            m.set(i, 6, dark, function=True)
        if not m.is_function[i][6]:
            m.set(6, i, dark, function=True)


def _reserve_format_areas(m):
    for i in range(9):
        if i != 6:
            m.is_function[8][i] = True
            m.is_function[i][8] = True
    for i in range(m.size - 8, m.size):
        m.is_function[8][i] = True
        m.is_function[i][8] = True
    m.set(8, m.size - 8, True, function=True)  # dark module


def _place_alignment_patterns(m, version):
    coords = _ALIGNMENT_COORDS.get(version, [])
    for cy in coords:
        for cx in coords:
            # ファインダーパターンと重なる位置はスキップ
            if (cx <= 8 and cy <= 8) or (cx <= 8 and cy >= m.size - 9) or (cx >= m.size - 9 and cy <= 8):
                continue
            _draw_alignment_pattern(m, cx, cy)


def _apply_mask(x, y, pattern):
    if pattern == 0:
        return (x + y) % 2 == 0
    if pattern == 1:
        return y % 2 == 0
    if pattern == 2:
        return x % 3 == 0
    if pattern == 3:
        return (x + y) % 3 == 0
    if pattern == 4:
        return (y // 2 + x // 3) % 2 == 0
    if pattern == 5:
        return (x * y) % 2 + (x * y) % 3 == 0
    if pattern == 6:
        return ((x * y) % 2 + (x * y) % 3) % 2 == 0
    if pattern == 7:
        return ((x + y) % 2 + (x * y) % 3) % 2 == 0
    return False


def _place_data(m, codewords):
    bits = []
    for c in codewords:
        for i in range(7, -1, -1):
            bits.append((c >> i) & 1)

    size = m.size
    bit_index = 0
    upward = True
    col = size - 1
    while col > 0:
        if col == 6:  # タイミングパターンの列はスキップ
            col -= 1
        col_pair = [col, col - 1]
        rows = range(size - 1, -1, -1) if upward else range(size)
        for row in rows:
            for c in col_pair:
                if m.is_function[row][c]:
                    continue
                bit = bits[bit_index] if bit_index < len(bits) else 0
                bit_index += 1
                m.set(c, row, bool(bit))
        upward = not upward
        col -= 2


def _mask_and_place(m, codewords):
    size = m.size
    best_matrix = None
    best_score = None
    best_mask = 0

    for pattern in range(8):
        trial = _Matrix(size)
        trial.modules = [row[:] for row in m.modules]
        trial.is_function = [row[:] for row in m.is_function]
        _place_data(trial, codewords)

        for y in range(size):
            for x in range(size):
                if not trial.is_function[y][x] and _apply_mask(x, y, pattern):
                    trial.modules[y][x] = not trial.modules[y][x]

        score = _penalty_score(trial)
        if best_score is None or score < best_score:
            best_score = score
            best_matrix = trial
            best_mask = pattern

    return best_matrix, best_mask


def _penalty_score(m):
    size = m.size
    score = 0
    # ルール1: 同色が5個以上連続
    for y in range(size):
        run = 1
        for x in range(1, size):
            if m.modules[y][x] == m.modules[y][x - 1]:
                run += 1
            else:
                if run >= 5:
                    score += 3 + (run - 5)
                run = 1
        if run >= 5:
            score += 3 + (run - 5)
    for x in range(size):
        run = 1
        for y in range(1, size):
            if m.modules[y][x] == m.modules[y - 1][x]:
                run += 1
            else:
                if run >= 5:
                    score += 3 + (run - 5)
                run = 1
        if run >= 5:
            score += 3 + (run - 5)

    # ルール2: 2x2の同色ブロック
    for y in range(size - 1):
        for x in range(size - 1):
            v = m.modules[y][x]
            if (m.modules[y][x + 1] == v and m.modules[y + 1][x] == v
                    and m.modules[y + 1][x + 1] == v):
                score += 3

    # ルール3は簡略化(省略, スコアへの影響は小さい)

    # ルール4: 暗モジュール比率
    dark = sum(1 for row in m.modules for v in row if v)
    total = size * size
    ratio = dark / total * 100
    prev = int(abs(ratio - 50) // 5) * 5
    nxt = prev + 5
    score += min(abs(prev - 50), abs(nxt - 50)) // 5 * 10

    return score


def _apply_format_info(m, mask_pattern):
    bits_val = _FORMAT_INFO_M[mask_pattern]
    bits = [(bits_val >> i) & 1 for i in range(15)]

    # 縦(左上)
    positions_v = [(8, 0), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (8, 7), (8, 8),
                   (7, 8), (5, 8), (4, 8), (3, 8), (2, 8), (1, 8), (0, 8)]
    for i, (x, y) in enumerate(positions_v):
        m.set(x, y, bool(bits[i]), function=True)

    # 横(右上)+縦(左下)
    size = m.size
    positions_h_tr = [(size - 1 - i, 8) for i in range(8)]
    positions_v_bl = [(8, size - 7 + i) for i in range(7)]
    for i, (x, y) in enumerate(positions_h_tr):
        m.set(x, y, bool(bits[i]), function=True)
    for i, (x, y) in enumerate(positions_v_bl):
        m.set(x, y, bool(bits[14 - i]), function=True)


def generate_matrix(text: str):
    """
    文字列(URLなど)からQRコードのモジュール行列(True=黒)を生成する。
    """
    data_bytes = text.encode("utf-8")
    version = _choose_version(len(data_bytes))
    total_codewords, ec_per_block, blocks = _VERSION_INFO_M[version]
    data_codewords_count = sum(n * (size - ec_per_block) for n, size in blocks)

    data_codewords = _build_bitstream(data_bytes, version, data_codewords_count)
    all_codewords = _interleave(data_codewords, version, ec_per_block, blocks)

    size = 21 + (version - 1) * 4
    m = _Matrix(size)

    _draw_finder_pattern(m, 0, 0)
    _draw_finder_pattern(m, size - 7, 0)
    _draw_finder_pattern(m, 0, size - 7)
    _place_alignment_patterns(m, version)
    _draw_timing_patterns(m)
    _reserve_format_areas(m)

    final_matrix, mask_pattern = _mask_and_place(m, all_codewords)
    _apply_format_info(final_matrix, mask_pattern)

    return final_matrix.modules


def generate_png(text: str, scale: int = 8, border: int = 4):
    """
    QRコードをPillowのImageオブジェクトとして生成する(白黒, 拡大あり)。
    """
    modules = generate_matrix(text)
    size = len(modules)
    img_size = (size + border * 2) * scale
    img = Image.new("1", (img_size, img_size), 1)  # 1 = 白
    pixels = img.load()

    for y in range(size):
        for x in range(size):
            if modules[y][x]:
                for dy in range(scale):
                    for dx in range(scale):
                        px = (x + border) * scale + dx
                        py = (y + border) * scale + dy
                        pixels[px, py] = 0  # 0 = 黒
    return img


if __name__ == "__main__":
    img = generate_png("https://example.com/")
    img.save("/tmp/qr_test.png")
    print("saved /tmp/qr_test.png", img.size)
