<div align="center">

# [CIE CIE TAIPEI](https://ciecietaipei.github.io/)

<p align="center">
  <img src="https://ciecietaipei.github.io/assets/ciecie_logo_circle.png" width="200" alt="Ciecie Logo">
</p>

### 我們將愜意帶進台北，柔和的光線，極簡的陳設，時間彷彿慢了下來。  
### 我們提供多樣化暖心餐點、微醺精選酒水繚繞，讓你在充滿設計感的空間中，享受愜意放鬆的用餐體驗，
### 這裡能讓您的每個感官都獲得滿足，準備好來 CIE CIE TAIPEI 享受美好夜晚了嗎？  


# 📍 地址：[台北市大安區信義路四段390號](https://maps.app.goo.gl/Nmh4xbvaxhVPRcJU9)
# ⏰ 營業時間：18:30 – 02:00（週五六至 03:00）
# 🥂 [立即線上 訂位點餐 / 外帶點餐](https://ciecietaipei.github.io/booking.html)
# ☎️ 02-27093446
</div>

</br></br></br></br>


# 👑 CIE CIE TAIPEI 網站 AI 餐飲暨訂位管理系統 ─ 白皮書

> **System Architecture & Feature Overview (系統架構與功能總覽)**

## 🏗️ 系統三大核心架構說明

兼顧「極致的網頁載入速度」、「絕對的資安防護」以及「零維護成本」，採用現代化分離式雲端架構
**「客製化前台」**（客人用的）、**「隱形安管大腦」**（雲端伺服器）、以及 **「老闆戰情室」**（後台管理）。

## 第一部分：**🌅 客製化前台黃金店面 (GitHub Pages)** (顧客端流暢的點餐與訂位體驗網頁)  

**核心價值：提供極致順暢的預約與點餐體驗，同時在第一線做好營運防護。**

  * **任務**：承載客人的視覺體驗與操作介面  
    * [index.html](https://ciecietaipei.github.io/index.html)  
    * [booking.html](https://ciecietaipei.github.io/booking.html)  
    * [foods.html](https://ciecietaipei.github.io/foods.html)  
    * [drinks.html](https://ciecietaipei.github.io/drinks.html)  
    * [environment.html](https://ciecietaipei.github.io/environment.html)  

   * **優勢**：全球 CDN 加速、永遠在線、完全免費，且網頁原始碼中不包含任何機密金鑰，安全性極高。  

1. **智慧分流與時段控管 「第一步：選擇服務 (內用/外帶) 的大按鈕畫面」**  
   * **功能說明**：系統會自動根據客人選擇「內用」或「外帶」，切換不同的營業時間限制。系統會自動過濾掉已過期的時間，並根據時段（白天、晚餐、宵夜）自動顯示對應的菜單。

<p align="center">
  <img src="./assets/README/001.png" width="600" alt="Ciecie booking screenshot">
</p>

2. **防護型購物車與訂金自動計算 「動態訂金試算引擎」**
   * **功能說明**：系統內建複雜的商業邏輯。
    * 5人(含)以上訂位，自動加收 $500/人 訂位金。  
    * 外帶餐點，自動計算為 100% 全額結帳。  
    * 內用若點選高價食材，按比例或全額收取預付金。

<p align="center">
  <img src="./assets/README/002.png" width="600" alt="Ciecie booking shopping cart screenshot">
    <img src="./assets/README/003.png" width="515" alt="Ciecie booking shopping cart screenshot">
</p>

3. **無縫接軌的 LINE Pay 體驗**
   * **功能說明**：確認訂單後，系統直接喚醒 LINE Pay 進行結帳，結帳完成後自動跳轉回官網並顯示成功動畫。

---

## 第二部分：**🧠 隱密智慧大腦與後台 (Hugging Face Spaces)**  (FastAPI 雲端核心)  

**核心價值：24 小時不休息的數位保鑣與收銀員，確保資料安全與金流準確。**

  * **任務**：運行 FastAPI 金流大腦與 Gradio 後台管理介面。  

  * **優勢**：作為「守門員」，負責在背景計算訂金、向 LINE Pay 申請收款連結、查核黑名單，並提供老闆專屬的視覺化管理介面，確保敏感邏輯不外流。  


1. **No-Show (放鳥) 黑名單自動攔截**  
  * **功能說明**：當客人按下送出時，大腦會瞬間去資料庫比對電話號碼。一旦發現是曾被老闆標記過「No-Show」的慣犯，即使他只訂 2 個人，系統也會**強制啟動防護機制，要求預付 $1000 訂金**，否則不予訂位。

<p align="center">
  <img src="./assets/README/004.png" width="600" alt="Ciecie booking no show screenshot">
</p>

2. **軍規級金流加密與自動對帳**

   * **功能說明**：每一筆 LINE Pay 交易都經過嚴格的 HMAC-SHA256 簽章加密，防止駭客竄改金額。付錢後自動將狀態改為「已付訂金」並通知老闆。

<p align="center">
  <img src="./assets/README/005.png" width="600" alt="Ciecie booking Line Pay screenshot">
</p>

---

## 第三部分：**🏦 雲端加密資料庫 (Supabase)** 老闆戰情室 (Admin 後台管理系統)

**核心價值：將複雜的營運數據化繁為簡，用手機或平板就能掌控全店狀況。**

  * **任務**：安全儲存訂單、菜單、顧客 No-Show 紀錄。  

  * **優勢**：銀行級別的加密防護，並提供強大的資料即時讀寫能力。  

1. **視覺化訂單管理卡片**

   * **功能說明**：捨棄傳統難讀的 Excel 表格，將每一筆訂單化為精美的「戰情卡片」。顏色標籤一目瞭然（綠色已確認、藍色待付款、紅色已取消/黑名單）。

<p align="center">
  <img src="./assets/README/006.png" width="600" alt="Ciecie booking Admin screenshot">
</p>

2. **一鍵查帳與補繳機制 (拯救流失訂單)**

   * **功能說明**：客人說他付了但系統沒顯示？老闆只需輸入訂單 ID 點擊「🔍 查 LINE Pay」，系統直接連線總部對帳。若客人忘記付款，點擊「🚀 發信/LINE」，系統會自動把專屬的「補繳費連結」寄給客人。

3. **免寫程式的「動態菜單」管理**

   * **功能說明**：換季換菜單、某道菜突然賣完？老闆隨時可以在後台新增餐點、設定價格、限制供應時段（例如宵夜限定），或是**「一鍵下架」**。前台顧客的手機畫面會在一秒內同步更新。

<p align="center">
  <img src="./assets/README/007.png" width="600" alt="Ciecie booking Admin screenshot">
</p>