import gradio as gr
import os
import requests
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone

# --- 1. 設定與初始化 ---
# ✅ 補回：設定台北時區 (UTC+8)
TAIPEI_TZ = timezone(timedelta(hours=8))

LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
LINE_ADMIN_ID = os.getenv("LINE_ADMIN_ID")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. 座位控管設定 (老闆可在此修改) ---
DEFAULT_LIMIT = 30 
SPECIAL_DAYS = {
    "2026-12-31": 10, # 跨年夜
    "2026-02-14": 15  # 情人節
}

# --- 3. 輔助函式 ---
def get_date_options():
    options = []
    # ✅ 修正：使用台北時間
    today = datetime.now(TAIPEI_TZ)
    weekdays = ["(一)", "(二)", "(三)", "(四)", "(五)", "(六)", "(日)"]
    for i in range(30): 
        current_date = today + timedelta(days=i)
        date_str = f"{current_date.strftime('%Y-%m-%d')} {weekdays[current_date.weekday()]}"
        options.append(date_str)
    return options

def update_time_slots(date_str):
    if not date_str: return gr.update(choices=[]), "請先選擇日期"
    try:
        clean_date_str = date_str.split(" ")[0] 
        date_obj = datetime.strptime(clean_date_str, "%Y-%m-%d")
        weekday = date_obj.weekday() 
    except: return gr.update(choices=[]), "日期格式錯誤"

    slots = ["18:30", "19:00", "19:30", "20:00", "20:30", 
             "21:00", "21:30", "22:00", "22:30", "23:00", "23:30", "00:00", "00:30", "01:00", "01:30"]
    if weekday == 4 or weekday == 5: slots.extend(["02:00", "02:30"])
    
    # 檢查剩餘座位
    clean_date = date_str.split(" ")[0]
    daily_limit = SPECIAL_DAYS.get(clean_date, DEFAULT_LIMIT)
    
    try:
        res = supabase.table("bookings").select("pax").eq("date", date_str).neq("status", "顧客已取消").execute()
        current_total = sum([item['pax'] for item in res.data])
        remaining = daily_limit - current_total
        status_msg = f"✨ {date_str} (剩餘座位: {remaining} 位)"
    except: status_msg = f"✨ {date_str}"

    return gr.update(choices=slots, value=slots[0] if slots else None), status_msg

# --- 4. 核心邏輯 ---
def get_line_id_from_url(request: gr.Request):
    """從網址參數讀取 line_id"""
    if request:
        return request.query_params.get("line_id", "")
    return ""

def handle_booking(name, tel, email, date_str, time, pax, remarks, line_id):
    # 👇👇👇 加入這一行除錯 👇👇👇
    print(f"🔥 DEBUG: 收到訂單，Name={name}, Line_ID={line_id}")
    if not name or not tel or not date_str or not time:
        return "⚠️ 請完整填寫必填欄位"

    # A. 檢查座位上限
    clean_date = date_str.split(" ")[0]
    daily_limit = SPECIAL_DAYS.get(clean_date, DEFAULT_LIMIT)
    try:
        res = supabase.table("bookings").select("pax").eq("date", date_str).neq("status", "顧客已取消").execute()
        current_total = sum([item['pax'] for item in res.data])
        if current_total + pax > daily_limit:
            return "⚠️ 抱歉，該時段剩餘座位不足，請調整人數或日期。"
    except: pass

    # B. 防重複提交
    try:
        existing = supabase.table("bookings").select("id").eq("tel", tel).eq("date", date_str).eq("time", time).neq("status", "顧客已取消").execute()
        if existing.data: return "⚠️ 您已預約過此時段，請勿重複提交。"
    except: pass

    # C. 寫入資料庫
    data = {
        "name": name, "tel": tel, "email": email, "date": date_str, "time": time, 
        "pax": pax, "remarks": remarks, "status": "待處理", 
        "user_id": line_id # 存入 LINE ID
    }
    
    try:
        supabase.table("bookings").insert(data).execute()
        
        # D. 發送 LINE Notify 給老闆 (⚠️ 這裡修改了格式)
        if LINE_ACCESS_TOKEN and LINE_ADMIN_ID:
            src = "🟢 LINE用戶" if line_id else "⚪ 訪客"
            # 處理備註：如果是空字串顯示 "無"
            note = remarks if remarks else "無"
            
            # 👇 新的漂亮格式 👇
            msg = (
                f"🔥 新訂位 ({src})\n"
                f"姓名：{name}\n"
                f"電話：{tel}\n"
                f"日期：{date_str}\n"
                f"時間：{time}\n"
                f"人數：{pax}人\n"
                f"備註：{note}"
            )
            requests.post("https://api.line.me/v2/bot/message/push", headers={"Authorization": f"Bearer {LINE_ACCESS_TOKEN}", "Content-Type": "application/json"}, json={"to": LINE_ADMIN_ID, "messages": [{"type": "text", "text": msg}]})
        
        return """<div style='text-align: center; color: #fff; padding: 20px; border: 1px solid #d4af37; border-radius: 8px; background: #222;'><h2 style='color: #d4af37; margin: 0;'>Request Received</h2><p style='margin: 10px 0;'>🥂 預約申請已提交</p><p style='font-size: 0.9em; color: #aaa;'>請留意 Email 確認信。</p></div>"""
    except Exception as e: return f"❌ 系統錯誤: {str(e)}"

# --- 5. Webhook (確認/取消邏輯 + 自動轉址到首頁) ---
def check_confirmation(request: gr.Request):
    if not request: return ""
    action = request.query_params.get('action')
    bid = request.query_params.get('id')
    
    # ✅ 修改這裡：目標改為官網首頁 (index.html)
    OFFICIAL_SITE = "https://ciecietaipei.github.io/index.html"
    
    if action == 'confirm' and bid:
        try:
            supabase.table("bookings").update({"status": "顧客已確認"}).eq("id", bid).execute()
            # 成功後，跳轉回首頁並帶上 status=confirmed
            return f"""<script>window.location.href = "{OFFICIAL_SITE}?status=confirmed";</script>"""
        except: 
            return "系統錯誤"
            
    elif action == 'cancel' and bid:
        try:
            supabase.table("bookings").update({"status": "顧客已取消"}).eq("id", bid).execute()
            # 取消後，跳轉回首頁並帶上 status=canceled
            return f"""<script>window.location.href = "{OFFICIAL_SITE}?status=canceled";</script>"""
        except: 
            return "系統錯誤"
            
    return ""

# --- 6. 介面 ---
theme = gr.themes.Soft(primary_hue="amber", neutral_hue="zinc").set(body_background_fill="#0F0F0F", block_background_fill="#1a1a1a", block_border_width="1px", block_border_color="#333", input_background_fill="#262626", input_border_color="#444", body_text_color="#E0E0E0", block_title_text_color="#d4af37", button_primary_background_fill="#d4af37", button_primary_text_color="#000000")
custom_css = "footer {display: none !important;} .gradio-container, .block, .row, .column { overflow: visible !important; } .options, .wrap .options { background-color: #262626 !important; border: 1px solid #d4af37 !important; z-index: 10000 !important; box-shadow: 0 5px 15px rgba(0,0,0,0.5); } .item:hover, .options .item:hover { background-color: #d4af37 !important; color: black !important; } .legal-footer { text-align: center; margin-top: 15px; padding-top: 15px; border-top: 1px solid #333; color: #666; font-size: 0.75rem; }"

with gr.Blocks(theme=theme, css=custom_css, title="Booking") as demo:
    # line_id_box = gr.Textbox(visible=False)
    # 👇 把 False 改成 True，並加上標籤方便辨識
    line_id_box = gr.Textbox(visible=True, label="【除錯用】接收到的 LINE ID")    
    confirm_msg_box = gr.HTML()
    demo.load(get_line_id_from_url, None, line_id_box)
    demo.load(check_confirmation, None, confirm_msg_box)

    with gr.Row():
        with gr.Column():
            gr.Markdown("### 📅 預約資訊 Booking Info")
            booking_date = gr.Dropdown(choices=get_date_options(), label="選擇日期 Select Date", interactive=True)
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
    gr.HTML("""<div class="legal-footer"><p style="margin-bottom: 5px;">© 2026 CIE CIE TAIPEI. All Rights Reserved.</p><p>內容涉及酒類產品訊息，請勿轉發分享給未達法定購買年齡者；未滿十八歲請勿飲酒。<br><strong>喝酒不開車，開車不喝酒。</strong></p></div>""")

    booking_date.change(update_time_slots, inputs=booking_date, outputs=[time_slot, status_box])
    submit_btn.click(handle_booking, inputs=[cust_name, cust_tel, cust_email, booking_date, time_slot, pax_count, cust_remarks, line_id_box], outputs=output_msg)

if __name__ == "__main__":
    demo.launch()