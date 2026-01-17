import gradio as gr
import os
import requests
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone

# 設定台北時區
TAIPEI_TZ = timezone(timedelta(hours=8))

# --- 1. 連線設定 ---
# 請確認 HF Secrets 裡都有設定這些變數
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
LINE_ADMIN_ID = os.getenv("LINE_ADMIN_ID")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# 建立 Supabase 連線
if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    print("⚠️ 警告：SUPABASE 環境變數未設定")

# --- 2. 輔助函式 (日期與時間) ---
def get_date_options():
    options = []
    # 這裡一定要加時區，不然會抓到 UTC 時間
    today = datetime.now(TAIPEI_TZ)
    weekdays = ["(一)", "(二)", "(三)", "(四)", "(五)", "(六)", "(日)"]
    for i in range(30): 
        current_date = today + timedelta(days=i)
        date_str = f"{current_date.strftime('%Y-%m-%d')} {weekdays[current_date.weekday()]}"
        options.append(date_str)
    return options

def update_time_slots(date_str):
    if not date_str:
        return gr.update(choices=[]), "請先選擇日期"
    try:
        clean_date_str = date_str.split(" ")[0] 
        date_obj = datetime.strptime(clean_date_str, "%Y-%m-%d")
        weekday = date_obj.weekday() 
    except:
        return gr.update(choices=[]), "日期格式錯誤"

    slots = ["18:30", "19:00", "19:30", "20:00", "20:30", 
             "21:00", "21:30", "22:00", "22:30", "23:00", "23:30", 
             "00:00", "00:30", "01:00"]
    
    if weekday == 4 or weekday == 5: 
        slots.extend(["01:30", "02:00", "02:30"])
        status_msg = f"✨ 已選擇 {date_str} (週末營業至 03:00)"
    else:
        slots.extend(["01:30"])
        status_msg = f"🌙 已選擇 {date_str} (平日營業至 02:00)"
        
    return gr.update(choices=slots, value=slots[0] if slots else None), status_msg

# --- 3. LINE 通知函式 ---
def send_line_notify(data):
    if not LINE_ACCESS_TOKEN or not LINE_ADMIN_ID: 
        return
    
    # 簡單的文字通知
    message = (
        f"🔥 新訂位通知 🔥\n"
        f"姓名：{data['name']}\n"
        f"電話：{data['tel']}\n"
        f"日期：{data['date']} {data['time']}\n"
        f"人數：{data['pax']} 位\n"
        f"Email：{data.get('email', '-')}\n"
        f"備註：{data.get('remarks', '無')}"
    )
    
    try:
        requests.post(
            "https://api.line.me/v2/bot/message/push",
            headers={
                "Authorization": f"Bearer {LINE_ACCESS_TOKEN}", 
                "Content-Type": "application/json"
            },
            json={
                "to": LINE_ADMIN_ID, 
                "messages": [{"type": "text", "text": message}]
            }
        )
    except Exception as e:
        print(f"LINE 發送失敗: {e}")

# --- 4. 核心邏輯：處理訂位 ---
def handle_booking(name, tel, email, date_str, time, pax, remarks):
    if not name or not tel or not date_str or not time:
        return "⚠️ 請完整填寫必填欄位 (姓名、電話、日期、時間)"
    
    # --- 1. 防呆機制：檢查是否重複提交 ---
    try:
        # 搜尋該電話在該時段的訂單
        existing = supabase.table("bookings").select("id")\
            .eq("tel", tel)\
            .eq("date", date_str)\
            .eq("time", time)\
            .neq("status", "顧客已取消")\
            .execute()
            
        if existing.data and len(existing.data) > 0:
            return "⚠️ 系統偵測到您已預約過此時段，請勿重複提交。"
    except Exception as e:
        print(f"Check duplicate error: {e}")
        pass

    # --- 準備資料 ---
    data = {
        "name": name, 
        "tel": tel, 
        "email": email, 
        "date": date_str, 
        "time": time, 
        "pax": pax, 
        "remarks": remarks, 
        "status": "待處理"
    }
    
    try:
        # 2. 寫入資料庫
        supabase.table("bookings").insert(data).execute()
        
        # 3. 發送 LINE 通知
        send_line_notify(data)
        
        # 4. 回傳成功訊息
        return """
        <div style='text-align: center; color: #fff; padding: 20px; border: 1px solid #d4af37; border-radius: 8px; background: #222;'>
            <h2 style='color: #d4af37; margin: 0;'>Request Received</h2>
            <p style='margin: 10px 0;'>🥂 預約申請已提交</p>
            <p style='font-size: 0.9em; color: #aaa;'>系統將發送確認信至您的 Email。</p>
            <p style='font-size: 0.85em; color: #ff5252; margin-top: 5px;'>
                (若未收到，請檢查您的<b>垃圾信件匣</b>)
            </p>
        </div>
        """
    except Exception as e:
        print(f"Error: {e}")
        return f"❌ 系統錯誤: {str(e)}"

# --- 5. 核心邏輯：處理確認連結 (Webhook) ---
# ⚠️ 修正重點：這裡是 check_confirmation，不是 send_confirmation_email
def check_confirmation(request: gr.Request):
    """
    當網址帶有 ?id=xx&action=confirm 或 ?id=xx&action=cancel 時觸發
    """
    if not request: return ""
    params = request.query_params
    action = params.get('action')
    bid = params.get('id')
    
    # --- 情況 A: 確認訂位 ---
    if action == 'confirm' and bid:
        try:
            # 更新資料庫狀態
            supabase.table("bookings").update({"status": "顧客已確認"}).eq("id", bid).execute()
            
            return f"""
            <script>
                document.addEventListener('DOMContentLoaded', function() {{
                    alert('✅ 感謝您！訂位已確認 (編號 {bid})');
                }});
            </script>
            <div style='padding:20px; background:#d4af37; color:black; text-align:center; margin-bottom:20px; border-radius:8px; font-weight:bold;'>
                🎉 感謝您的確認！我們期待您的光臨。 (訂單編號: {bid})
            </div>
            """
        except Exception as e:
            print(f"Confirm Error: {e}")
            return ""

    # --- 情況 B: 取消訂位 ---
    elif action == 'cancel' and bid:
        try:
            # 更新資料庫狀態
            supabase.table("bookings").update({"status": "顧客已取消"}).eq("id", bid).execute()
            
            return f"""
            <script>
                document.addEventListener('DOMContentLoaded', function() {{
                    alert('已為您取消訂位 (編號 {bid})');
                }});
            </script>
            <div style='padding:20px; background:#333; border: 1px solid #ff5252; color:#ff5252; text-align:center; margin-bottom:20px; border-radius:8px;'>
                🚫 訂位已取消。<br>期待您下次有機會再來訪。
            </div>
            """
        except Exception as e:
            print(f"Cancel Error: {e}")
            return ""
            
    return ""

# --- 6. 介面設定 (Theme & CSS) ---
theme = gr.themes.Soft(
    primary_hue="amber",
    neutral_hue="zinc",
    font=[gr.themes.GoogleFont("Playfair Display"), "ui-sans-serif", "sans-serif"],
).set(
    body_background_fill="#0F0F0F",
    block_background_fill="#1a1a1a",
    block_border_width="1px",
    block_border_color="#333",
    input_background_fill="#262626",
    input_border_color="#444",
    body_text_color="#E0E0E0",
    block_title_text_color="#d4af37",
    button_primary_background_fill="#d4af37",
    button_primary_text_color="#000000",
)

custom_css = """
footer {display: none !important;}
.gradio-container, .block, .row, .column { overflow: visible !important; }
.options, .wrap .options {
    background-color: #262626 !important;
    border: 1px solid #d4af37 !important;
    z-index: 10000 !important;
    box-shadow: 0 5px 15px rgba(0,0,0,0.5);
}
.item, .options .item { color: #E0E0E0 !important; padding: 8px 12px !important; }
.item:hover, .item.selected, .options .item:hover { background-color: #d4af37 !important; color: black !important; }
input:focus, .dropdown-trigger:focus-within { border-color: #d4af37 !important; box-shadow: 0 0 8px rgba(212, 175, 55, 0.4) !important; }
h3 { border-bottom: 1px solid #444; padding-bottom: 5px; margin-bottom: 10px; }
.legal-footer {
    text-align: center; margin-top: 15px; padding-top: 15px; border-top: 1px solid #333; color: #666; font-size: 0.75rem; line-height: 1.5; font-family: sans-serif;
}
.legal-footer strong { color: #888; }
"""

# --- 7. 介面佈局 (完整版) ---
with gr.Blocks(theme=theme, css=custom_css, title="Booking") as demo:
    
    # [隱藏] 用來接收 URL 確認參數的區塊
    confirm_msg_box = gr.HTML()
    
    # 頁面載入時，執行 check_confirmation
    demo.load(check_confirmation, inputs=None, outputs=confirm_msg_box)

    with gr.Row():
        with gr.Column():
            gr.Markdown("### 📅 預約資訊 Booking Info")

            date_options = get_date_options()
            booking_date = gr.Dropdown(choices=date_options, label="選擇日期 Select Date", interactive=True)
            pax_count = gr.Slider(minimum=1, maximum=10, value=2, step=1, label="用餐人數 Guest Count")

        with gr.Column():
             gr.Markdown("### 🕰️ 選擇時段 Time Slot")
             status_box = gr.Markdown("請先選擇日期...", visible=True)
             time_slot = gr.Dropdown(choices=[], label="可用時段 Available Time", interactive=True)

    gr.HTML("<div style='height: 10px'></div>")

    gr.Markdown("### 👤 聯絡人資料 Contact，收到確認 E-Mail 並點擊 確認出席 才算訂位成功")
    with gr.Group():
        with gr.Row():
            cust_name = gr.Textbox(label="訂位姓名 Name *", placeholder="ex. 王小明")
            cust_tel = gr.Textbox(label="手機號碼 Phone *", placeholder="ex. 0912-xxx-xxx")
        
        with gr.Row():
            cust_email = gr.Textbox(label="電子信箱 E-mail (接收確認信用，請記得檢查垃圾信件匣。)", placeholder="example@gmail.com")
        with gr.Row():
            cust_remarks = gr.Textbox(label="備註 Remarks (過敏/慶生/特殊需求)", lines=2)

    gr.HTML("<div style='height: 15px'></div>")
    
    submit_btn = gr.Button("確認預約 Request Booking (系統會記錄是否曾 No Show)", size="lg", variant="primary")
    output_msg = gr.HTML()

    # 頁尾警語
    gr.HTML("""
    <div class="legal-footer">
        <p style="margin-bottom: 5px;">© 2026 CIE CIE TAIPEI. All Rights Reserved.</p>
        <p>內容涉及酒類產品訊息，請勿轉發分享給未達法定購買年齡者；未滿十八歲請勿飲酒。<br>
        <strong>喝酒不開車，開車不喝酒。</strong></p>
    </div>
    """)

    # --- 互動事件綁定 ---
    # 1. 日期改變 -> 更新時段
    booking_date.change(update_time_slots, inputs=booking_date, outputs=[time_slot, status_box])
    
    # 2. 送出按鈕 -> 處理訂位
    submit_btn.click(
        handle_booking, 
        inputs=[cust_name, cust_tel, cust_email, booking_date, time_slot, pax_count, cust_remarks], 
        outputs=output_msg
    )

if __name__ == "__main__":
    demo.launch()