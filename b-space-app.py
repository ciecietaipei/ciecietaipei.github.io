import gradio as gr
import os
import pandas as pd
import requests
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone

# ✅ 補回：設定台北時區
TAIPEI_TZ = timezone(timedelta(hours=8))

# --- 設定 ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GAS_MAIL_URL = os.getenv("GAS_MAIL_URL")
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
PUBLIC_SPACE_URL = "https://deeplearning101-ciecietaipei.hf.space" 

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

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
            html = f"""
            <div style="padding:20px; background:#111; color:#d4af37; border-radius:10px; max-width:600px; margin:0 auto; font-family:sans-serif;">
                <h2 style="border-bottom:1px solid #d4af37; padding-bottom:15px; text-align:center;">Cié Cié Taipei</h2>
                <p>{booking['name']} 您好，已為您保留座位：</p>
                <div style="background:#222; padding:15px; border-radius:8px;">
                    <ul style="color:#eee; list-style:none; padding:0; margin:0; line-height:1.8;">
                        <li>📅 {booking['date']} | ⏰ {booking['time']}</li>
                        <li>👥 {booking['pax']} 位</li>
                        <li>📝 {booking.get('remarks') or '無'}</li>
                    </ul>
                </div>
                <div style="text-align:center; margin-top:25px;">
                    <a href="{confirm_link}" style="background:#d4af37; color:#000; padding:12px 25px; text-decoration:none; border-radius:5px; margin:0 10px; font-weight:bold;">✅ 確認出席</a>
                    <a href="{cancel_link}" style="border:1px solid #ff5252; color:#ff5252; padding:11px 24px; text-decoration:none; border-radius:5px; margin:0 10px; font-weight:bold;">🚫 取消</a>
                </div>
            </div>
            """
            requests.post(GAS_MAIL_URL, json={"to": email, "subject": f"[{booking['date']}] 訂位確認", "htmlBody": html, "name": "Cié Cié Taipei"})
            log_msg += f"✅ Email ok "
        
        # 2. LINE 發送
        if user_id and len(str(user_id)) > 10 and LINE_ACCESS_TOKEN:
            try:
                line_msg = f"【訂位確認】{booking['name']} 您好\n已為您保留 {booking['date']} {booking['time']} ({booking['pax']}位)。\n\n如需取消請直接回覆，或點擊 Email 中的連結。期待您的光臨！"
                requests.post("https://api.line.me/v2/bot/message/push", headers={"Authorization": f"Bearer {LINE_ACCESS_TOKEN}", "Content-Type": "application/json"}, json={"to": user_id, "messages": [{"type": "text", "text": line_msg}]})
                log_msg += "| ✅ LINE ok"
            except: log_msg += "| ❌ LINE fail"
        else: log_msg += "| ℹ️ No LINE ID"

        supabase.table("bookings").update({"status": "已發確認信"}).eq("id", booking_id).execute()
        return log_msg
    except Exception as e: return f"❌ Error: {str(e)}"

with gr.Blocks(title="Admin") as demo:
    gr.Markdown("# 🍷 訂位管理後台")
    refresh_btn = gr.Button("🔄 重新整理")
    booking_table = gr.Dataframe(interactive=False)
    with gr.Row():
        id_input = gr.Number(label="訂單 ID", precision=0)
        action_btn = gr.Button("📧 發送確認信 (Hybrid)", variant="primary")
    log_output = gr.Textbox(label="結果")
    refresh_btn.click(get_bookings, outputs=booking_table)
    action_btn.click(send_confirmation_hybrid, inputs=id_input, outputs=log_output)

if __name__ == "__main__":
    demo.launch(auth=(ADMIN_USER or "admin", ADMIN_PASSWORD or "123456"))