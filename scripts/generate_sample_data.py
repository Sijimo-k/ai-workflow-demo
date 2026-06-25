"""デモ用のサンプル受注CSVを3モールぶん生成する。

実務の壁を再現するため、わざと以下を散らしてある:
  - 文字コード … 楽天 / Yahoo は CP932、Shopify は UTF-8
  - 列名 / 日付書式 / ステータス語彙 … モールごとに別物
  - 未入金・発送済みの注文を混ぜる … 発送対象抽出が効くことを見せる

実行: python scripts/generate_sample_data.py
"""

from __future__ import annotations

import csv
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "sample"

RAKUTEN_ROWS = [
    # 注文番号, 注文日, 購入者名, メール, 商品名, 単価, 個数, 〒, 住所, 入金状態, 発送状況
    ["R-2026-0001", "2026/06/20", "山田 太郎", "taro.yamada@example.com", "有機ドリップコーヒー 12袋", "1,800", "2", "150-0001", "東京都渋谷区神宮前1-2-3", "入金済", "未発送"],
    ["R-2026-0002", "2026/06/20", "佐藤 花子", "hanako.sato@example.com", "ステンレスタンブラー 450ml", "2,480", "1", "060-0001", "北海道札幌市中央区北1条西2-3", "入金済", "未発送"],
    ["R-2026-0003", "2026/06/21", "鈴木 一郎", "ichiro.suzuki@example.com", "コーヒー豆 エチオピア 200g", "1,200", "3", "231-0001", "神奈川県横浜市中区新港1-1", "未入金", "未発送"],
    ["R-2026-0004", "2026/06/21", "高橋 美咲", "misaki.t@example.com", "ハンドドリップセット", "4,980", "1", "460-0008", "愛知県名古屋市中区栄3-4-5", "入金済", "発送済"],
]

YAHOO_ROWS = [
    # ご注文ID, 注文日時, お名前, メール, 商品名, 価格, 数量, 〒, 住所, 決済状況, 出荷状況
    ["yahoo-88001", "2026/06/20 09:15:22", "田中 健", "ken.tanaka@example.com", "カフェインレス コーヒー 10袋", "1,500", "1", "530-0001", "大阪府大阪市北区梅田2-1-1", "完了", "未出荷"],
    ["yahoo-88002", "2026/06/21 14:33:05", "伊藤 さくら", "sakura.ito@example.com", "コーヒーミル 手動式", "3,200", "1", "810-0001", "福岡県福岡市中央区天神1-2-3", "完了", "未出荷"],
    ["yahoo-88003", "2026/06/22 18:02:47", "渡辺 大輔", "daisuke.w@example.com", "ギフトボックス 詰め合わせ", "5,400", "1", "980-0001", "宮城県仙台市青葉区中央1-1-1", "未決済", "未出荷"],
]

SHOPIFY_ROWS = [
    # Name, Created at, Billing Name, Email, Lineitem name, Lineitem price, Lineitem quantity, Shipping Zip, Shipping Address1, Financial Status, Fulfillment Status
    ["#1001", "2026-06-21 09:12:33 +0900", "Kenji Nakamura", "kenji.n@example.com", "Cold Brew Bottle 500ml", "2800", "2", "650-0001", "兵庫県神戸市中央区加納町4-5-6", "paid", ""],
    ["#1002", "2026-06-22 11:45:10 +0900", "Yuki Kobayashi", "yuki.k@example.com", "Single Origin Beans 1kg", "4500", "1", "700-0001", "岡山県岡山市北区表町1-2-3", "paid", ""],
    ["#1003", "2026-06-22 20:30:55 +0900", "Aoi Matsumoto", "aoi.m@example.com", "Travel Tumbler Set", "3600", "1", "900-0001", "沖縄県那覇市おもろまち1-1-1", "paid", "fulfilled"],
    ["#1004", "2026-06-23 08:05:00 +0900", "Sora Inoue", "sora.i@example.com", "Drip Coffee Gift 20pcs", "3000", "2", "330-0001", "埼玉県さいたま市大宮区桜木町1-1", "pending", ""],
]


def _write(path: Path, header: list[str], rows: list[list[str]], encoding: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding=encoding, newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"  wrote {path}  ({encoding}, {len(rows)} rows)")


def main() -> None:
    print("サンプル受注CSVを生成します:")
    _write(
        OUT / "rakuten_orders.csv",
        ["注文番号", "注文日", "購入者名", "購入者メールアドレス", "商品名", "単価", "個数", "送付先郵便番号", "送付先住所", "入金状態", "発送状況"],
        RAKUTEN_ROWS,
        encoding="cp932",
    )
    _write(
        OUT / "yahoo_orders.csv",
        ["ご注文ID", "注文日時", "お名前", "メールアドレス", "商品名", "価格", "数量", "お届け先郵便番号", "お届け先住所", "決済状況", "出荷状況"],
        YAHOO_ROWS,
        encoding="cp932",
    )
    _write(
        OUT / "shopify_orders.csv",
        ["Name", "Created at", "Billing Name", "Email", "Lineitem name", "Lineitem price", "Lineitem quantity", "Shipping Zip", "Shipping Address1", "Financial Status", "Fulfillment Status"],
        SHOPIFY_ROWS,
        encoding="utf-8",
    )
    print("完了。")


if __name__ == "__main__":
    main()
