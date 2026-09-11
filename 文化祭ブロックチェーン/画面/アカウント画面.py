# -*- coding: utf-8 -*-
"""
アカウント画面.py
-----------------
アカウント作成と残高確認を行う画面(Flask Blueprint)。

生徒が各自のスマートフォンからアクセスする運用を想定し、
アカウント作成時にそのブラウザ(Flaskのセッションcookieは端末ごとに別)へ
「自分のアカウント」を記憶させる。これにより、各自のスマホでは
毎回一覧から自分を探す必要がなく、送金・採掘画面で自動的に
自分のアカウントが選択された状態になる。

セッションには公開鍵をそのまま保存せず、状態.py の encode_key() で
1行化した値を保存する(cookieは改行を含められないため)。
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import 状態 as state  # noqa: E402

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "アカウント"))
from アカウント import Account  # noqa: E402

from flask import Blueprint, render_template, request, redirect, url_for, flash, session

account_bp = Blueprint("account", __name__)

SESSION_KEY = "my_public_key_encoded"
SESSION_USERNAME = "my_username"


def get_my_account():
    """
    現在のブラウザ(セッション)に紐づく「自分のアカウント」情報を返す。
    未作成の場合はNone。
    """
    encoded = session.get(SESSION_KEY)
    if not encoded:
        return None
    public_key = state.decode_key(encoded)
    account = state.account_repo.load_account(public_key)
    return account


@account_bp.route("/account", methods=["GET"])
def account_page():
    accounts = state.account_repo.load_all_accounts()
    accounts_view = []
    for acc in accounts:
        balance = state.blockchain.get_balance(acc["public_key"])
        accounts_view.append({
            "username": acc["username"],
            "public_key": acc["public_key"],
            "public_key_short": acc["public_key"][:60] + "...",
            "balance": balance,
            "is_me": session.get(SESSION_USERNAME) == acc["username"]
                     and state.decode_key(session.get(SESSION_KEY, "")) == acc["public_key"],
        })
    return render_template(
        "account.html",
        accounts=accounts_view,
        my_username=session.get(SESSION_USERNAME),
    )


@account_bp.route("/account/create", methods=["POST"])
def account_create():
    username = request.form.get("username", "").strip()
    if not username:
        flash("ユーザー名を入力してください。")
        return redirect(url_for("account.account_page"))

    account = Account.create_new(username)
    state.account_repo.save_account(
        public_key=account.get_public_key(),
        username=account.username,
        private_key=account.get_private_key(),
    )

    # このブラウザ(スマホ)に「自分のアカウント」として記憶させる
    session[SESSION_KEY] = state.encode_key(account.get_public_key())
    session[SESSION_USERNAME] = account.username

    flash(f"アカウント「{username}」を作成しました。あなたのアカウントとして記憶しました。")
    return redirect(url_for("account.me_page"))


@account_bp.route("/me", methods=["GET"])
def me_page():
    """マイページ: このスマホ(セッション)に紐づく自分のアカウントを表示する。"""
    my_account = get_my_account()
    if not my_account:
        flash("まだアカウントを作成していません。下のフォームから作成してください。")
        return redirect(url_for("account.account_page"))

    balance = state.blockchain.get_balance(my_account["public_key"])
    return render_template(
        "me.html",
        username=my_account["username"],
        public_key=my_account["public_key"],
        public_key_encoded=state.encode_key(my_account["public_key"]),
        balance=balance,
    )


@account_bp.route("/logout", methods=["POST"])
def logout():
    """
    このブラウザに記憶している「自分のアカウント」を解除する。
    同じ端末を複数人で使い回す場合などに利用する。
    """
    session.pop(SESSION_KEY, None)
    session.pop(SESSION_USERNAME, None)
    flash("このスマホに記憶していたアカウント情報を解除しました。")
    return redirect(url_for("account.account_page"))
