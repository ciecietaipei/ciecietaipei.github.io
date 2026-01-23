import gradio as gr
import os
import pandas as pd
import requests
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone

# 設定台北時區
TAIPEI_TZ = timezone(timedelta(hours=8))

# --- 設定 ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GAS_MAIL_URL = os.getenv("GAS_MAIL_URL")
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
# ⚠️ 請確認這是您 Space A 的正確網址 (結尾不要有斜線)
PUBLIC_SPACE_URL = "https://deeplearning101-ciecietaipei.hf.space" 

# 取得帳密 (若沒設定則使用預設值)
REAL_ADMIN_USER = os.getenv("ADMIN_USER") or "Deep Learning 101"
REAL_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD") or "2016-11-11"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_bookings():
    res = supabase.table("bookings").select("*").order("created_at", desc=True).execute()
    if not res.data: return pd.DataFrame()
    df = pd.DataFrame(res.data)
    cols = ['id', 'date', 'time', 'name', 'tel', 'email', 'pax', 'remarks', 'status', 'user_id']
    for c in cols: 
        if c not in df.columns: df[c] = ""
    return df[cols]

def send_confirmation_hybrid(booking_id):
    try:
        res = supabase.table("bookings").select("*").eq("id", booking_id).execute()
        if not res.data: return "❌ 找不到訂單"
        booking = res.data[0]
        email, user_id = booking.get('email'), booking.get('user_id')
        log_msg = ""
        
        confirm_link = f"{PUBLIC_SPACE_URL}/?id={booking_id}&action=confirm"
        cancel_link = f"{PUBLIC_SPACE_URL}/?id={booking_id}&action=cancel"

        # 1. Email 發送
        if email and "@" in email:
            try:
                html = f"""
                <div style="padding: 20px; background: #111; color: #d4af37; border-radius: 10px; max-width: 600px; margin: 0 auto; font-family: sans-serif;">
                    <h2 style="border-bottom: 1px solid #d4af37; padding-bottom: 15px; text-align: center; letter-spacing: 2px;">Cié Cié Taipei</h2>
                    <p style="font-size: 16px; margin-top: 20px; color: #eee;">{booking['name']} 您好，已為您保留座位：</p>
                    <div style="background: #222; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #d4af37;">
                        <ul style="color: #eee; list-style: none; padding: 0; margin: 0; line-height: 2;">
                            <li>📅 日期：<strong style="color:#fff;">{booking['date']}</strong></li>
                            <li>⏰ 時間：<strong style="color:#fff;">{booking['time']}</strong></li>
                            <li>👥 人數：<strong style="color:#fff;">{booking['pax']} 位</strong></li>
                            <li>📝 備註：{booking.get('remarks') or '無'}</li>
                        </ul>
                    </div>
                    <table width="100%" border="0" cellspacing="0" cellpadding="0">
                        <tr>
                            <td align="center">
                                <a href="{confirm_link}" style="display: inline-block; background: #d4af37; color: #000; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; margin-right: 10px;">✅ 確認出席</a>
                                <a href="{cancel_link}" style="display: inline-block; border: 1px solid #ff5252; color: #ff5252; padding: 11px 29px; text-decoration: none; border-radius: 5px; font-weight: bold; margin-left: 10px;">🚫 取消</a>
                            </td>
                        </tr>
                    </table>
                    <hr style="border: 0; border-top: 1px solid #333; margin-top: 30px;">
                    <p style="color: #666; font-size: 12px; text-align: center;">如需更改，請直接回覆此信件。</p>
                </div>
                """
                requests.post(GAS_MAIL_URL, json={"to": email, "subject": f"[{booking['date']}] 訂位確認 - Cié Cié Taipei", "htmlBody": html, "name": "Cié Cié Taipei"})
                log_msg += f"✅ Email ok "
            except Exception as e:
                log_msg += f"⚠️ Email 失敗: {e} "
        
        # 2. LINE 發送
        if not LINE_ACCESS_TOKEN:
            log_msg += "| ⚠️ 未設定 LINE_ACCESS_TOKEN"
        elif not user_id or len(str(user_id)) < 10:
            log_msg += "| ℹ️ 無 LINE ID"
        else:
            try:
                flex_payload = {
                    "type": "flex",
                    "altText": "您有一筆訂位確認通知",
                    "contents": {
                        "type": "bubble",
                        "styles": { "header": {"backgroundColor": "#222222"}, "body": {"backgroundColor": "#2c2c2c"}, "footer": {"backgroundColor": "#2c2c2c"} },
                        "header": { "type": "box", "layout": "vertical", "contents": [ {"type": "text", "text": "Cié Cié Taipei", "color": "#d4af37", "weight": "bold", "size": "xl", "align": "center"} ] },
                        "body": {
                            "type": "box", "layout": "vertical",
                            "contents": [
                                {"type": "text", "text": "訂位確認", "weight": "bold", "size": "lg", "color": "#ffffff", "align": "center", "margin": "md"},
                                {"type": "separator", "margin": "lg", "color": "#444444"},
                                {"type": "box", "layout": "vertical", "margin": "lg", "spacing": "sm", "contents": [
                                    {"type": "box", "layout": "baseline", "spacing": "sm", "contents": [ {"type": "text", "text": "姓名", "color": "#aaaaaa", "size": "sm", "flex": 2}, {"type": "text", "text": f"{booking['name']}", "wrap": True, "color": "#ffffff", "size": "sm", "flex": 4} ]},
                                    {"type": "box", "layout": "baseline", "spacing": "sm", "contents": [ {"type": "text", "text": "日期", "color": "#aaaaaa", "size": "sm", "flex": 2}, {"type": "text", "text": f"{booking['date']}", "wrap": True, "color": "#ffffff", "size": "sm", "flex": 4} ]},
                                    {"type": "box", "layout": "baseline", "spacing": "sm", "contents": [ {"type": "text", "text": "時間", "color": "#aaaaaa", "size": "sm", "flex": 2}, {"type": "text", "text": f"{booking['time']}", "wrap": True, "color": "#ffffff", "size": "sm", "flex": 4} ]},
                                    {"type": "box", "layout": "baseline", "spacing": "sm", "contents": [ {"type": "text", "text": "人數", "color": "#aaaaaa", "size": "sm", "flex": 2}, {"type": "text", "text": f"{booking['pax']} 位", "wrap": True, "color": "#ffffff", "size": "sm", "flex": 4} ]}
                                ]}
                            ]
                        },
                        "footer": {
                            "type": "box", "layout": "vertical", "spacing": "sm",
                            "contents": [
                                { "type": "button", "style": "primary", "color": "#d4af37", "height": "sm", "action": { "type": "uri", "label": "✅ 確認出席", "uri": confirm_link } },
                                { "type": "button", "style": "secondary", "height": "sm", "color": "#aaaaaa", "action": { "type": "uri", "label": "🚫 取消訂位", "uri": cancel_link } }
                            ]
                        }
                    }
                }
                r = requests.post("https://api.line.me/v2/bot/message/push", headers={"Authorization": f"Bearer {LINE_ACCESS_TOKEN}", "Content-Type": "application/json"}, json={"to": user_id, "messages": [flex_payload]})
                if r.status_code == 200: log_msg += "| ✅ LINE Flex ok"
                else: log_msg += f"| ❌ LINE 錯誤: {r.text}"
            except Exception as e: log_msg += f"| ❌ LINE 例外: {e}"

        supabase.table("bookings").update({"status": "已發確認信"}).eq("id", booking_id).execute()
        return log_msg
    except Exception as e: return f"❌ Error: {str(e)}"

# --- 登入邏輯 (回傳 HTML 字串來控制顏色) ---
def check_login(user, password):
    if user == REAL_ADMIN_USER and password == REAL_ADMIN_PASSWORD:
        return {
            login_row: gr.update(visible=False),
            admin_row: gr.update(visible=True),
            error_msg: ""
        }
    else:
        # ✅ 使用 HTML span 標籤來顯示紅色，而不是在 gr.Markdown 用 style 參數
        return {
            error_msg: "<span style='color: red'>❌ 帳號或密碼錯誤</span>"
        }

# --- 🔥 新增 CSS：強制表格寬度與捲軸 ---
# 這段 CSS 會讓表格內容不換行，並在手機上出現水平捲軸
custom_css = """
table { 
    min-width: 1200px !important; 
}
td, th { 
    white-space: nowrap !important; 
    padding: 8px !important;
}
.table-wrap {
    overflow-x: auto !important;
}
"""

# --- 介面開始 (加入 css 參數) ---
with gr.Blocks(title="Admin", css=custom_css) as demo:
    
    # 1. 登入介面
    with gr.Group(visible=True) as login_row:
        gr.Markdown("# 🔒 請登入後台")
        with gr.Row():
            username_input = gr.Textbox(label="帳號 Username", placeholder="Enter username")
            password_input = gr.Textbox(label="密碼 Password", type="password", placeholder="Enter password")
        login_btn = gr.Button("登入 Login", variant="primary")
        error_msg = gr.Markdown("")
        
    # 2. 後台介面
    with gr.Group(visible=False) as admin_row:
        gr.Markdown("# 🍷 訂位管理後台 (Dashboard)")
        refresh_btn = gr.Button("🔄 重新整理")
        # 表格這裡會自動套用上面的 CSS
        booking_table = gr.Dataframe(interactive=False)
        with gr.Row():
            id_input = gr.Number(label="訂單 ID", precision=0)
            action_btn = gr.Button("📧 發送確認信 (Hybrid)", variant="primary")
        log_output = gr.Textbox(label="結果")
        
        refresh_btn.click(get_bookings, outputs=booking_table)
        action_btn.click(send_confirmation_hybrid, inputs=id_input, outputs=log_output)

    # 3. 綁定登入按鈕
    login_btn.click(
        check_login, 
        inputs=[username_input, password_input], 
        outputs=[login_row, admin_row, error_msg]
    )

if __name__ == "__main__":
    demo.launch()