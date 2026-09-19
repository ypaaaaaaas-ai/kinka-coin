# -*- coding: utf-8 -*-
"""
送金画面.py
-----------
コイン送金画面(Flask Blueprint)。

生徒が各自のスマホから送金する運用を想定し、「送金者」はフォームで
選ばせず、そのブラウザにひもづく「自分のアカウント」(アカウント画面.py の
セッション)を必ず送金者として使う。これにより、他人のアカウントから
勝手に送金する操作(なりすまし)ができないようにしている。

流れ:
    1. 受取者・金額をフォームから受け取る(送金者は常にセッションから取得)。
    2. 送金者の秘密鍵(DB保存分)を使って取引データに電子署名する。
    3. blockchain.add_transaction() で「受信時は必ず検証」を行い、
       未承認取引として一時保存する。
    4. 他ノードへブロードキャストする。
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import 状態 as state  # noqa: E402

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "ブロックチェーン"))
from 取引 import Transaction  # noqa: E402

from flask import Blueprint, render_template, request, redirect, url_for, flash

from アカウント画面 import get_my_account  # noqa: E402

send_bp = Blueprint("send", __name__)


@send_bp.route("/send", methods=["GET"])
def send_page():
    my_account = get_my_account()
    if not my_account:
        flash("送金するには、先にログインしてください。")
        return redirect(url_for("account.login_page"))

    my_balance = state.blockchain.get_balance(my_account["public_key"])

    others = [
        {
            "username": acc["username"],
            "public_key_encoded": state.encode_key(acc["public_key"]),
        }
        for acc in state.account_repo.load_all_accounts()
        if acc["public_key"] != my_account["public_key"]
    ]

    # ---- QRコードからの自動入力(/send?user=けん&amount=300) ----
    # スマホのカメラで受け取り用QRを読み取ると、このクエリ付きで
    # 送金画面が開く。受取人と金額をあらかじめフォームに設定する。
    prefill_to = None
    prefill_name = None
    prefill_amount = None
    qr_notice = None

    qr_user = request.args.get("user", "").strip()
    if qr_user:
        target = state.account_repo.find_by_username(qr_user)
        if target is None:
            qr_notice = f"QRコードの受取人「{qr_user}」が見つかりません。アカウントが削除された可能性があります。"
        elif target["public_key"] == my_account["public_key"]:
            qr_notice = "これはあなた自身の受け取り用QRコードです。友だちに読み込んでもらいましょう。"
        else:
            prefill_to = state.encode_key(target["public_key"])
            prefill_name = target["username"]
            raw_amount = request.args.get("amount", "").strip()
            if raw_amount:
                try:
                    value = int(raw_amount)
                    if value > 0:
                        prefill_amount = value
                except ValueError:
                    pass  # 不正な金額は無視して手入力してもらう

    return render_template(
        "send.html",
        my_username=my_account["username"],
        my_balance=my_balance,
        others=others,
        pending_count=len(state.blockchain.pending_transactions),
        prefill_to=prefill_to,
        prefill_name=prefill_name,
        prefill_amount=prefill_amount,
        qr_notice=qr_notice,
    )


@send_bp.route("/send", methods=["POST"])
def send_submit():
    my_account = get_my_account()
    if not my_account:
        flash("送金するには、先にログインしてください。")
        return redirect(url_for("account.login_page"))

    sender_key = my_account["public_key"]
    receiver_key_encoded = request.form.get("receiver")
    amount_raw = request.form.get("amount", "0")

    receiver_key = state.decode_key(receiver_key_encoded) if receiver_key_encoded else None

    try:
        amount = int(amount_raw)
    except ValueError:
        flash("送金額は数値で入力してください。")
        return redirect(url_for("send.send_page"))

    if not receiver_key:
        flash("受取者を選択してください。")
        return redirect(url_for("send.send_page"))

    if sender_key == receiver_key:
        flash("自分自身には送金できません。")
        return redirect(url_for("send.send_page"))

    if amount <= 0:
        flash("送金額は1以上を指定してください。")
        return redirect(url_for("send.send_page"))

    balance = state.blockchain.get_balance(sender_key)
    if balance < amount:
        flash(f"残高不足です(残高: {balance} コイン)。")
        return redirect(url_for("send.send_page"))

    transaction = Transaction(sender=sender_key, receiver=receiver_key, amount=amount)
    transaction.sign_transaction(my_account["private_key"])

    tx_dict = transaction.to_dict()
    accepted = state.blockchain.add_transaction(tx_dict)

    if not accepted:
        flash("取引の検証に失敗しました(署名または残高を確認してください)。")
        return redirect(url_for("send.send_page"))

    state.persist_pending()
    state.broadcaster.broadcast_transaction(tx_dict)

    flash(f"{amount} コインを送金しました(採掘されるまで未承認取引として保持されます)。")
    return redirect(url_for("send.send_page"))
