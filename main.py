import flet as ft
import pandas as pd
from datetime import datetime
import os

def main(page: ft.Page):
    print("✅ APP 正在啟動畫面中...") 
    
    # --- 基本設定 ---
    page.title = "代購小幫手 (統計面板版)"
    page.window_width = 480
    page.window_height = 850
    page.scroll = "auto"
    page.theme_mode = ft.ThemeMode.LIGHT

    orders = [] 

    # 雲端暫存設定
    if not os.path.exists("assets"):
        os.makedirs("assets")

    # --- 邏輯函數 ---

    def slider_change(e):
        rate_value_text.value = f"{rate_slider.value:.2f}"
        page.update()

    def status_change(e):
        if payment_dropdown.value == "已付訂金":
            deposit_field.disabled = False
            deposit_field.value = ""
            deposit_field.focus()
        else:
            deposit_field.disabled = True
            deposit_field.value = ""
        page.update()

    def calculate_buyer_total(buyer_name):
        total = 0
        for order in orders:
            if order['購買人'] == buyer_name:
                total += order['台幣總價']
        return total

    def add_click(e):
        if not buyer_field.value:
            page.snack_bar = ft.SnackBar(ft.Text("❌ 請輸入購買人姓名"))
            page.snack_bar.open = True
            page.update()
            return
        
        if not name_field.value or not price_field.value:
            page.snack_bar = ft.SnackBar(ft.Text("❌ 請輸入商品名稱和日幣價格"))
            page.snack_bar.open = True
            page.update()
            return

        try:
            jpy = float(price_field.value)
            if custom_rate_field.value:
                final_rate = float(custom_rate_field.value)
            else:
                final_rate = rate_slider.value

            extra_fee = int(extra_fee_field.value) if extra_fee_field.value else 0
            twd = int(jpy * final_rate) + extra_fee

            deposit_amount = 0
            if payment_dropdown.value == "已付訂金":
                if not deposit_field.value:
                    page.snack_bar = ft.SnackBar(ft.Text("❌ 請輸入訂金金額"))
                    page.snack_bar.open = True
                    page.update()
                    return
                deposit_amount = int(deposit_field.value)
            elif payment_dropdown.value == "已付款":
                deposit_amount = twd

            balance_due = twd - deposit_amount

        except ValueError:
            page.snack_bar = ft.SnackBar(ft.Text("❌ 價格或格式錯誤"))
            page.snack_bar.open = True
            page.update()
            return

        current_buyer_total = calculate_buyer_total(buyer_field.value) + twd
        is_free_shipping = current_buyer_total >= 3500
        free_shipping_tag = " (🎉已達免運)" if is_free_shipping else ""

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        order_data = {
            "購買人": buyer_field.value,
            "商品名稱": name_field.value,
            "備註": note_field.value,
            "日幣": jpy,
            "計算匯率": final_rate,
            "額外費用": extra_fee,
            "台幣總價": twd,
            "付款狀態": payment_dropdown.value,
            "已付訂金": deposit_amount,
            "待付尾款": balance_due,
            "累積金額": current_buyer_total,
            "網址": url_field.value,
            "時間": timestamp
        }
        orders.append(order_data)

        # UI 更新 - 加入列表
        if payment_dropdown.value == "已付訂金":
            status_color = "orange"
            status_text = f"訂金${deposit_amount}"
        elif payment_dropdown.value == "已付款":
            status_color = "green"
            status_text = "已付清"
        else:
            status_color = "red"
            status_text = "未付款"
        
        history_list.controls.insert(0, 
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(name="person", size=16, color="blue"),
                        ft.Text(f"{buyer_field.value}", weight="bold", size=16),
                        ft.Container(
                            content=ft.Text(status_text, size=12, color="white", weight="bold"),
                            bgcolor=status_color, padding=5, border_radius=5
                        ),
                    ]),
                    ft.Text(f"商品: {name_field.value}", size=15, weight="bold"),
                    ft.Row([
                        ft.Text(f"¥{int(jpy)} x {final_rate}", color="grey", size=12),
                        ft.Icon(name="arrow_right_alt", size=12, color="grey"),
                        ft.Text(f"NT$ {twd}", color="red", size=18, weight="bold"),
                    ]),
                    ft.Text(f"目前累計: ${current_buyer_total} {free_shipping_tag}", color="blue" if is_free_shipping else "grey", size=13),
                ]),
                padding=15,
                border=ft.border.all(1, "grey"),
                border_radius=10,
                bgcolor="white",
            )
        )
        
        # 清空輸入框
        name_field.value = ""
        price_field.value = ""
        url_field.value = ""
        note_field.value = ""
        custom_rate_field.value = ""
        extra_fee_field.value = ""
        deposit_field.value = ""
        if payment_dropdown.value == "已付訂金":
             deposit_field.focus()
        
        page.snack_bar = ft.SnackBar(ft.Text(f"✅ 加入成功！總價 ${twd}"))
        page.snack_bar.open = True
        page.update()

    # ==========================================
    # 👇👇👇 新增功能：開啟統計儀表板 👇👇👇
    # ==========================================
    def open_stats_dialog(e):
        if not orders:
            page.snack_bar = ft.SnackBar(ft.Text("❌ 目前沒有訂單資料"))
            page.snack_bar.open = True
            page.update()
            return

        # 1. 資料整理 (Group by 購買人)
        stats_data = {}
        for order in orders:
            name = order['購買人']
            if name not in stats_data:
                stats_data[name] = {
                    'items': [], 
                    'total_twd': 0, 
                    'total_deposit': 0, 
                    'total_balance': 0
                }
            stats_data[name]['items'].append(order)
            stats_data[name]['total_twd'] += order['台幣總價']
            stats_data[name]['total_deposit'] += order['已付訂金']
            stats_data[name]['total_balance'] += order['待付尾款']

        # 2. 建立 UI 內容
        stats_controls = []
        
        for name, data in stats_data.items():
            # 判斷免運
            is_free = data['total_twd'] >= 3500
            shipping_tag = ft.Container(content=ft.Text("免運費", size=12, color="white"), bgcolor="green", padding=5, border_radius=5) if is_free else ft.Container(content=ft.Text("未達免運", size=12, color="white"), bgcolor="grey", padding=5, border_radius=5)

            # 該人的商品清單
            item_rows = []
            for item in data['items']:
                # 付款狀態標籤顏色
                p_status = item['付款狀態']
                p_color = "green" if p_status == "已付款" else ("orange" if p_status == "已付訂金" else "red")
                
                item_rows.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(f"• {item['商品名稱']}", weight="bold", expand=True),
                                ft.Text(f"${item['台幣總價']}", color="red", weight="bold"),
                            ]),
                            ft.Row([
                                ft.Text(f"匯率: {item['計算匯率']}", size=12, color="grey"),
                                ft.Container(content=ft.Text(p_status, size=10, color="white"), bgcolor=p_color, padding=2, border_radius=3)
                            ], alignment="spaceBetween")
                        ]),
                        padding=5,
                        border=ft.border.only(bottom=ft.border.BorderSide(1, "grey200"))
                    )
                )

            # 該人的總結卡片
            card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(name="person", color="blue"),
                        ft.Text(f"{name}", size=20, weight="bold"),
                        shipping_tag
                    ]),
                    ft.Divider(),
                    ft.Column(item_rows), # 商品明細
                    ft.Divider(),
                    ft.Row([
                        ft.Text(f"總金額: ${data['total_twd']}", size=16, weight="bold"),
                        ft.Column([
                            ft.Text(f"已付: ${data['total_deposit']}", color="green", size=12),
                            ft.Text(f"未付: ${data['total_balance']}", color="red", size=12, weight="bold"),
                        ], alignment="end")
                    ], alignment="spaceBetween")
                ]),
                padding=15,
                border=ft.border.all(1, "blue100"),
                border_radius=10,
                bgcolor="blue50",
                margin=ft.margin.only(bottom=10)
            )
            stats_controls.append(card)

        # 3. 顯示彈跳視窗
        dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("📊 買家結算統計"),
            content=ft.Container(
                content=ft.Column(stats_controls, scroll="auto"),
                width=400,
                height=500, # 固定高度，內容可捲動
            ),
            actions=[
                ft.TextButton("關閉", on_click=lambda e: page.close(dlg_modal)),
            ],
            actions_alignment="end",
        )
        page.open(dlg_modal)

    # 匯出 Excel (保留原本功能)
    def export_click(e):
        if not orders: return
        try:
            filename = f"Daigou_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            filepath = os.path.join("assets", filename)
            df = pd.DataFrame(orders)
            cols = ["購買人", "商品名稱", "備註", "台幣總價", "付款狀態", "已付訂金", "待付尾款", "日幣", "計算匯率", "額外費用", "累積金額", "網址", "時間"]
            for col in cols:
                if col not in df.columns: df[col] = ""
            df = df[cols]
            df.to_excel(filepath, index=False)
            page.launch_url(f"/{filename}")
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"❌ 錯誤: {ex}"))
            page.snack_bar.open = True
            page.update()

    # --- UI 元件設計 ---
    
    rate_slider = ft.Slider(min=0.26, max=0.30, divisions=40, value=0.28, label="{value}", on_change=slider_change)
    rate_value_text = ft.Text("0.28", size=20, weight="bold", color="blue")
    rate_section = ft.Container(
        content=ft.Column([ft.Text("💰 一般匯率 (0.26 ~ 0.30)", weight="bold"), ft.Row([rate_slider, rate_value_text], alignment="center")]),
        bgcolor="blue50", padding=10, border_radius=10
    )

    buyer_field = ft.TextField(label="購買人", icon="person", width=130)
    deposit_field = ft.TextField(label="訂金$", width=90, keyboard_type="number", disabled=True, hint_text="金額")
    payment_dropdown = ft.Dropdown(
        width=130, label="狀態", value="未付款",
        options=[ft.dropdown.Option("未付款"), ft.dropdown.Option("已付款"), ft.dropdown.Option("已付訂金")],
        on_change=status_change
    )
    buyer_row = ft.Row([buyer_field, payment_dropdown, deposit_field], alignment="spaceBetween")

    name_field = ft.TextField(label="商品名稱")
    price_field = ft.TextField(label="日幣價格 (JPY)", keyboard_type="number", suffix_text="円")
    url_field = ft.TextField(label="商品網址 (選填)")
    note_field = ft.TextField(label="備註 (規格/顏色/重物)", icon="edit_note")

    custom_rate_field = ft.TextField(label="特殊匯率", width=180, keyboard_type="number", hint_text="例 0.5")
    extra_fee_field = ft.TextField(label="額外費用", width=180, keyboard_type="number", suffix_text="元")
    advanced_row = ft.Container(
        content=ft.Column([
            ft.Text("⚖️ 特殊/重物計價 (選填)", size=14, weight="bold", color="orange"),
            ft.Row([custom_rate_field, extra_fee_field], alignment="spaceBetween")
        ]),
        bgcolor="orange50", padding=10, border_radius=10
    )

    btn_add = ft.ElevatedButton("加入訂單", icon="add_shopping_cart", on_click=add_click, bgcolor="blue", color="white", height=50, width=450)
    history_list = ft.ListView(expand=True, spacing=10, padding=10)
    
    # 新增按鈕區：統計報表 + 匯出
    btn_stats = ft.ElevatedButton("📊 查看統計報表", on_click=open_stats_dialog, bgcolor="purple", color="white", height=50, expand=True)
    btn_export = ft.ElevatedButton("📥 匯出 Excel", on_click=export_click, bgcolor="green", color="white", height=50, expand=True)
    action_row = ft.Row([btn_stats, btn_export], spacing=10)

    page.add(
        ft.Text("🇯🇵 代購系統 (完整版)", size=25, weight="bold", text_align="center"),
        rate_section,
        ft.Divider(height=10, color="transparent"),
        buyer_row,
        name_field,
        price_field,
        url_field,
        note_field,
        advanced_row,
        ft.Container(height=5),
        btn_add,
        ft.Divider(),
        ft.Text("📋 本次訂單列表", size=16, weight="bold"),
        ft.Container(content=history_list, height=200, bgcolor="grey100", border_radius=10), # 高度稍微縮小給按鈕
        action_row # 放置雙按鈕
    )

app = ft.app(target=main, export_asgi_app=True, assets_dir="assets")