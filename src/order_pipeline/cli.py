"""コマンドラインから受注処理パイプライン一式を実行するエントリポイント。

例:
    python -m order_pipeline \\
        --rakuten data/sample/rakuten_orders.csv \\
        --yahoo   data/sample/yahoo_orders.csv \\
        --shopify data/sample/shopify_orders.csv \\
        --outdir  output
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from .exporters import export_mails, export_shipping_list_excel, export_unified_csv
from .loaders import load_rakuten, load_shopify, load_yahoo
from .models import Order
from .pipeline import integrate, shipping_targets, summarize

# 手作業での1件あたり処理時間（Before）と自動化後（After）。効果試算の前提値。
MANUAL_SECONDS_PER_ORDER = 5 * 60
AUTO_SECONDS_PER_ORDER = 30


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="order_pipeline",
        description="複数ECモールの受注CSVを統合し、発送対象抽出・出荷リスト・メール文面を自動生成する。",
    )
    parser.add_argument("--rakuten", type=Path, help="楽天 受注CSV(CP932)")
    parser.add_argument("--yahoo", type=Path, help="Yahoo!ショッピング 受注CSV(CP932)")
    parser.add_argument("--shopify", type=Path, help="Shopify 受注CSV(UTF-8)")
    parser.add_argument("--outdir", type=Path, default=Path("output"), help="出力先ディレクトリ")
    return parser.parse_args(argv)


def _load_all(args: argparse.Namespace) -> list[list[Order]]:
    """指定されたモールのCSVだけを読み込む。"""
    loaded: list[list[Order]] = []
    if args.rakuten:
        loaded.append(load_rakuten(args.rakuten))
    if args.yahoo:
        loaded.append(load_yahoo(args.yahoo))
    if args.shopify:
        loaded.append(load_shopify(args.shopify))
    return loaded


def run(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    loaded = _load_all(args)
    if not loaded:
        print("エラー: --rakuten / --yahoo / --shopify のいずれかを指定してください。")
        return 1

    started = time.perf_counter()
    orders = integrate(*loaded)
    targets = shipping_targets(orders)
    summary = summarize(orders, targets)

    outdir: Path = args.outdir
    csv_path = export_unified_csv(orders, outdir / "unified_orders.csv")
    xlsx_path = export_shipping_list_excel(targets, outdir / "shipping_list.xlsx")
    mail_paths = export_mails(targets, outdir / "mails")
    elapsed = time.perf_counter() - started

    _print_report(summary, csv_path, xlsx_path, mail_paths, elapsed)
    return 0


def _print_report(summary, csv_path, xlsx_path, mail_paths, elapsed) -> None:
    manual = summary.total_orders * MANUAL_SECONDS_PER_ORDER
    auto = summary.total_orders * AUTO_SECONDS_PER_ORDER
    saved_min = (manual - auto) / 60

    print("=" * 52)
    print(" EC受注処理 自動化パイプライン 実行結果")
    print("=" * 52)
    print(f"  統合受注件数　 : {summary.total_orders} 件")
    print(f"  発送対象件数　 : {summary.target_orders} 件")
    print(f"  対象外件数　　 : {summary.excluded_orders} 件（{summary.excluded_reason_hint}）")
    print(f"  発送対象 合計額: {summary.target_amount:,} 円")
    print("-" * 52)
    print("  生成物:")
    print(f"    統合CSV    : {csv_path}")
    print(f"    出荷リスト : {xlsx_path}")
    print(f"    メール文面 : {len(mail_paths)} 通 -> {mail_paths[0].parent if mail_paths else '(なし)'}")
    print("-" * 52)
    print("  効果試算（手作業比）:")
    print(f"    手作業想定 : {summary.total_orders}件 × {MANUAL_SECONDS_PER_ORDER // 60}分 = {summary.total_orders * MANUAL_SECONDS_PER_ORDER // 60} 分")
    print(f"    自動処理   : 実測 {elapsed:.2f} 秒")
    print(f"    削減見込み : 約 {saved_min:.0f} 分")
    print("=" * 52)


if __name__ == "__main__":
    raise SystemExit(run())
