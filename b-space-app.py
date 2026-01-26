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
PUBLIC_SPACE_URL = "https://deeplearning101-ciecietaipei.hf.space" 

# 取得帳密
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

# --- 登入邏輯 ---
def check_login(user, password):
    if user == REAL_ADMIN_USER and password == REAL_ADMIN_PASSWORD:
        return {
            login_row: gr.update(visible=False),
            admin_row: gr.update(visible=True),
            error_msg: ""
        }
    else:
        return {
            error_msg: "<span style='color: red'>❌ 帳號或密碼錯誤</span>"
        }

# --- 🟢 [JS 核心邏輯]：層層檢查，殺掉紅框，保留綠框 ---
fix_scroll_js = """
function() {
    const applyFix = () => {
        const root = document.querySelector('#booking_table');
        if (!root) return;

        // 1. 殺掉外層捲軸 (Red Scrollbar)
        // 找到所有包在表格外面的 div，只要不是直接包著 table 的，通通 hidden
        const allDivs = root.querySelectorAll('div');
        allDivs.forEach(div => {
            // 如果這個 div 裡面還有一個 table-wrap，或者它本身就是外層包裝
            // 而且它不是 table 的直接父層
            const hasInnerTable = div.querySelector('table');
            if (hasInnerTable && window.getComputedStyle(div).overflowX === 'auto') {
                div.style.overflowX = 'hidden'; 
                div.style.maxWidth = '100%';
            }
        });
        
        // 確保最外層也是 hidden
        root.style.overflowX = 'hidden';

        // 2. 保留內層捲軸 (Green Scrollbar)
        const table = root.querySelector('table');
        if (table) {
            // 強制設定表格寬度，確保內容撐開
            table.style.width = '1500px'; 
            table.style.minWidth = '1500px'; 
            table.style.tableLayout = 'fixed';

            // 找到直接父層 (Green Scrollbar 所在位置)
            const parent = table.parentElement;
            if (parent) {
                parent.style.overflowX = 'auto'; // 開啟
                parent.style.maxWidth = '100vw'; // 限制寬度
                parent.style.display = 'block';
            }
        }
    };

    // 啟動時執行
    applyFix();
    // 循環執行以對抗 Gradio 的動態渲染
    setInterval(applyFix, 500);
}
"""

# --- 🔥 [CSS] 定寬 + 換行 + 隱藏全域捲軸 ---
custom_css = """
/* 1. 全域與元件外層：殺死紅框捲軸 */
body, .gradio-container {
    overflow-x: hidden !important; /* 殺死瀏覽器捲軸 */
    max-width: 100vw !important;
}

#booking_table {
    overflow: hidden !important; /* 殺死元件捲軸 */
    max-width: 100% !important;
    border: none !important;
    padding: 0 !important;
}

/* 2. 中間層：確保沒有任何中間人偷偷加捲軸 */
#booking_table .wrap, 
#booking_table .svelte-12cmxck { 
    overflow-x: hidden !important;
    max-width: 100% !important;
}

/* 3. 內層 (綠框位置)：唯一允許捲動的地方 */
#booking_table .table-wrap, 
#booking_table tbody {
    overflow-x: auto !important;
    overflow-y: hidden !important;
    max-width: 100vw !important; /* 確保不超過螢幕 */
    border: 1px solid #444 !important;
}

/* 4. 表格本體：撐開它！ */
#booking_table table {
    table-layout: fixed !important;
    width: 1500px !important; /* 總寬度 */
    min-width: 1500px !important;
}

/* 5. 欄位內容：自動換行 */
#booking_table th, #booking_table td {
    white-space: normal !important;
    word-break: break-all !important;
    overflow-wrap: break-word !important;
    vertical-align: top !important;
    padding: 8px 5px !important;
    border: 1px solid #444 !important;
    font-size: 13px !important;
    line-height: 1.4 !important;
}

/* 6. 個別欄位寬度 */
#booking_table th:nth-child(1), #booking_table td:nth-child(1) { width: 60px !important; }
#booking_table th:nth-child(2), #booking_table td:nth-child(2) { width: 170px !important; }
#booking_table th:nth-child(3), #booking_table td:nth-child(3) { width: 80px !important; }
#booking_table th:nth-child(4), #booking_table td:nth-child(4) { width: 120px !important; }
#booking_table th:nth-child(5), #booking_table td:nth-child(5) { width: 120px !important; }
#booking_table th:nth-child(6), #booking_table td:nth-child(6) { width: 250px !important; }
#booking_table th:nth-child(7), #booking_table td:nth-child(7) { width: 50px !important; }
#booking_table th:nth-child(8), #booking_table td:nth-child(8) { width: 180px !important; }
#booking_table th:nth-child(9), #booking_table td:nth-child(9) { width: 120px !important; }
#booking_table th:nth-child(10), #booking_table td:nth-child(10) { width: 320px !important; }
"""

# --- 介面開始 ---
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
        
        # ✅ elem_id 保持為 booking_table
        booking_table = gr.Dataframe(interactive=False, elem_id="booking_table")
        
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
    
    # 🔥🔥🔥 執行 JS 強制修正 🔥🔥🔥
    demo.load(None, js=fix_scroll_js)

if __name__ == "__main__":
    demo.launch()