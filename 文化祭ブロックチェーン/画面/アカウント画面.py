# -*- coding: utf-8 -*-
"""
アカウント画面.py
-----------------
アカウント作成・ログイン・マイページを行う画面(Flask Blueprint)。

ユーザー名+パスワードでのログイン制に改修した版:
- アカウント作成時は「ユーザー名+パスワード(+確認用)」を受け取り、
  パスワードは 暗号/パスワード.py でPBKDF2ハッシュ化して保存する。
- 作成直後は自動的にログイン済みにする(会場での体験を止めないため)。
- 2回目以降のアクセスや、別端末・ログアウト後は /login で
  ユーザー名+パスワードによるログインを行う。
- ユーザー名はシステム内で一意(重複登録不可)。これにより
  「ユーザー名+パスワード」で本人を一意に特定できる。

セッションには公開鍵をそのまま保存せず、状態.py の encode_key() で
1行化した値を保存する(cookieは改行を含められないため)。
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import 状態 as state  # noqa: E402

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "アカウント"))
from アカウント import Account  # noqa: E402

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "暗号"))
from パスワード import verify_password  # noqa: E402

from flask import Blueprint, render_template, request, redirect, url_for, flash, session

account_bp = Blueprint("account", __name__)

SESSION_KEY = "my_public_key_encoded"
SESSION_USERNAME = "my_username"

USERNAME_MAX_LENGTH = 30   # アカウント作成フォーム(maxlength)と合わせる
PASSWORD_MIN_LENGTH = 4    # 展示運用向けの最低文字数。厳しくしたい場合はここを変更


def get_my_account():
    """
    現在のブラウザ(セッション)に紐づく「ログイン中のアカウント」情報を返す。
    未ログインの場合はNone。
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
            "has_password": bool(acc.get("password_hash")),
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
    """新規アカウント作成。ユーザー名+パスワードを受け取り、作成後自動ログインする。"""
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    password_confirm = request.form.get("password_confirm", "")

    if not username:
        flash("ユーザー名を入力してください。")
        return redirect(url_for("account.account_page"))

    if len(username) > USERNAME_MAX_LENGTH:
        flash(f"ユーザー名は{USERNAME_MAX_LENGTH}文字以内で入力してください。")
        return redirect(url_for("account.account_page"))

    # ログインを成り立たせるため、ユーザー名は一意である必要がある
    if state.account_repo.username_exists(username):
        flash(f"ユーザー名「{username}」は既に使われています。別の名前でお試しください。")
        return redirect(url_for("account.account_page"))

    if len(password) < PASSWORD_MIN_LENGTH:
        flash(f"パスワードは{PASSWORD_MIN_LENGTH}文字以上で入力してください。")
        return redirect(url_for("account.account_page"))

    if password != password_confirm:
        flash("パスワードが確認用と一致しません。")
        return redirect(url_for("account.account_page"))

    account = Account.create_new(username, password)
    state.account_repo.save_account(
        public_key=account.get_public_key(),
        username=account.username,
        private_key=account.get_private_key(),
        password_hash=account.get_password_hash(),
        salt=account.get_salt(),
    )

    # 作成したアカウントで自動ログイン(このスマホに記憶させる)
    session[SESSION_KEY] = state.encode_key(account.get_public_key())
    session[SESSION_USERNAME] = account.username

    flash(f"アカウント「{username}」を作成し、ログインしました。")
    return redirect(url_for("account.me_page"))


@account_bp.route("/login", methods=["GET"])
def login_page():
    """ログイン画面。既にログイン済みならマイページへ飛ばす。"""
    if get_my_account():
        return redirect(url_for("account.me_page"))
    return render_template("login.html")


@account_bp.route("/login", methods=["POST"])
def login():
    """ユーザー名+パスワードでログインする。"""
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username or not password:
        flash("ユーザー名とパスワードを入力してください。")
        return redirect(url_for("account.login_page"))

    account = state.account_repo.find_by_username(username)
    # 「ユーザー名が存在しない」「パスワードが違う」の区別を画面上では出さない
    # (アカウント存在の推測を難しくする一般的な配慮)
    if account is None:
        flash("ユーザー名またはパスワードが違います。")
        return redirect(url_for("account.login_page"))

    password_hash = account.get("password_hash")
    salt = account.get("salt")
    if not password_hash or not salt:
        # パスワード制導入前に作られた旧アカウント。運営が /admin の全初期化を
        # 行うか、改めて新規アカウントを作ってもらう。
        flash("このアカウントにはパスワードが未設定です。新しいアカウントを作成してください。")
        return redirect(url_for("account.login_page"))

    if not verify_password(password, password_hash, salt):
        flash("ユーザー名またはパスワードが違います。")
        return redirect(url_for("account.login_page"))

    session[SESSION_KEY] = state.encode_key(account["public_key"])
    session[SESSION_USERNAME] = account["username"]

    flash(f"{username} さんとしてログインしました。")
    return redirect(url_for("account.me_page"))


@account_bp.route("/me", methods=["GET"])
def me_page():
    """マイページ: ログイン中のアカウント情報を表示する。"""
    my_account = get_my_account()
    if not my_account:
        flash("マイページを見るにはログインしてください。")
        return redirect(url_for("account.login_page"))

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
    ログアウトする。このブラウザ(セッション)のログイン状態だけを解除し、
    アカウント自体は消えない(再度 /login からログインできる)。
    """
    session.pop(SESSION_KEY, None)
    session.pop(SESSION_USERNAME, None)
    flash("ログアウトしました。")
    return redirect(url_for("account.login_page"))
