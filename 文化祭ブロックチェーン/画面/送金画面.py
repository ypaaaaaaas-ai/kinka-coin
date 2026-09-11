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
        flash("送金するには、先に自分のアカウントを作成してください。")
        return redirect(url_for("account.account_page"))

    my_balance = state.blockchain.get_balance(my_account["public_key"])

    others = [
        {
            "username": acc["username"],
            "public_key_encoded": state.encode_key(acc["public_key"]),
        }
        for acc in state.account_repo.load_all_accounts()
        if acc["public_key"] != my_account["public_key"]
    ]

    return render_template(
        "send.html",
        my_username=my_account["username"],
        my_balance=my_balance,
        others=others,
        pending_count=len(state.blockchain.pending_transactions),
    )


@send_bp.route("/send", methods=["POST"])
def send_submit():
    my_account = get_my_account()
    if not my_account:
        flash("送金するには、先に自分のアカウントを作成してください。")
        return redirect(url_for("account.account_page"))

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
