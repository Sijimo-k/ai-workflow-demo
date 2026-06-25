"""統合・抽出・集計のコア処理。すべて副作用のない純関数で、テストしやすくする。"""

from __future__ import annotations

from dataclasses import dataclass

from .models import Order


def integrate(*order_lists: list[Order]) -> list[Order]:
    """複数モールの受注を1リストに統合し、注文日時の昇順に並べる。"""
    merged: list[Order] = []
    for orders in order_lists:
        merged.extend(orders)
    merged.sort(key=lambda o: o.order_date)
    return merged


def shipping_targets(orders: list[Order]) -> list[Order]:
    """発送対象（入金済み かつ 未発送）だけを抽出する。"""
    return [o for o in orders if o.is_shipping_target]


@dataclass(frozen=True)
class Summary:
    """処理結果のサマリ。CLI 表示と効果測定（工数削減）に使う。"""

    total_orders: int
    target_orders: int
    target_amount: int
    excluded_orders: int

    @property
    def excluded_reason_hint(self) -> str:
        return "未入金 または 発送済み"


def summarize(orders: list[Order], targets: list[Order]) -> Summary:
    """統合結果と発送対象から集計サマリを作る。"""
    return Summary(
        total_orders=len(orders),
        target_orders=len(targets),
        target_amount=sum(o.amount for o in targets),
        excluded_orders=len(orders) - len(targets),
    )
