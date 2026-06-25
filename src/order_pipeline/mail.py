"""顧客向け発送通知メールの文面生成（テンプレート方式）。

LLM を使わずテンプレート＋差し込みで生成する。API キー不要・完全再現・テスト容易で、
「定型業務の自動化」というデモの主旨に最も合うため。差し込み項目は正規化済み Order
からのみ取るので、文面のブレや転記ミスが構造的に起こらない。
"""

from __future__ import annotations

from .models import Order, Source

# モールごとの差出名（顧客にはモール名で届くのが自然なため）。
_SHOP_NAME: dict[Source, str] = {
    Source.RAKUTEN: "楽天市場店",
    Source.YAHOO: "Yahoo!ショッピング店",
    Source.SHOPIFY: "公式オンラインストア",
}

_TEMPLATE = """\
{customer_name} 様

この度は{shop_name}をご利用いただき、誠にありがとうございます。
ご注文いただいた商品を本日発送いたしましたので、ご案内申し上げます。

■ ご注文内容
　注文番号：{order_id}
　商品名　：{product_name}
　数量　　：{quantity}
　金額　　：{amount:,}円（税込）

■ お届け先
　〒{postal_code}
　{address}

商品の到着まで、いましばらくお待ちくださいませ。
ご不明な点がございましたら、本メールにご返信ください。

{shop_name}
"""


def render_mail(order: Order) -> str:
    """1受注ぶんの発送通知メール文面を生成する。"""
    return _TEMPLATE.format(
        customer_name=order.customer_name,
        shop_name=_SHOP_NAME[order.source],
        order_id=order.order_id,
        product_name=order.product_name,
        quantity=order.quantity,
        amount=order.amount,
        postal_code=order.postal_code,
        address=order.address,
    )


def mail_filename(order: Order) -> str:
    """メール文面の保存ファイル名。モールと注文番号で一意にする。"""
    safe_id = order.order_id.replace("#", "").replace("/", "-")
    return f"{order.source.value}_{safe_id}.txt"
