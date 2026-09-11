// main.js - 共通の小さなUI挙動

document.addEventListener("DOMContentLoaded", () => {
  // フラッシュメッセージを数秒後にフェードアウト
  document.querySelectorAll(".flash").forEach((el, i) => {
    setTimeout(() => {
      el.style.transition = "opacity 0.6s ease";
      el.style.opacity = "0";
    }, 4500 + i * 300);
  });

  // 採掘ボタン: 送信中に「採掘中...」表示に切り替える(Proof of Workは時間がかかるため)
  const mineForm = document.querySelector("#mine-form");
  if (mineForm) {
    mineForm.addEventListener("submit", () => {
      const btn = mineForm.querySelector("button[type=submit]");
      if (btn) {
        btn.disabled = true;
        btn.textContent = "採掘中...(ハッシュを計算しています)";
      }
    });
  }
});
