<div align="center">

// ======================================================
// 全域設定區 (請務必修改這三行)
// ======================================================

// 1. LINE Channel Access Token (請填入您的 Token)
const CHANNEL_ACCESS_TOKEN = "您的_LINE_Channel_Access_Token_貼在這裡";

// 2. Google Sheet ID (請填入您的試算表 ID)
const SHEET_ID = "您的_Google_Sheet_ID_貼在這裡";

// 3. Web App 網址 (部署後取得的網址，請填入)
const WEB_APP_URL = "您的_Web_App_網址_貼在這裡";

// ======================================================
// 核心程式碼開始 (已針對 C 欄空白、Email 在 F 欄修正)
// ======================================================

const ss = SpreadsheetApp.openById(SHEET_ID);
// 為了保險起見，這裡指定抓取名稱為 "Form Responses 1" 或 "表單回應 1" 的工作表
// 如果您的工作表名稱改過，請修改下面這行
var sheet = ss.getSheetByName("表單回應 1"); 
if (!sheet) sheet = ss.getSheets()[0]; // 如果找不到名字，就抓第一個

// ------------------------------------------------------
// 功能 1：當有新訂位 (Google Form 提交) 時觸發
// ------------------------------------------------------
function onFormSubmit(e) {
  var lastRow = sheet.getLastRow();
  
  // 1. 自動產生訂位編號 (ID)
  var uniqueId = "R-" + Math.random().toString(36).substr(2, 5).toUpperCase();
  
  // 2. 把 ID 寫入 A 欄 (第 1 欄)
  sheet.getRange(lastRow, 1).setValue(uniqueId);
  
  // 3. 把狀態預設為 "待處理" 寫入 J 欄 (第 10 欄)
  sheet.getRange(lastRow, 10).setValue("待處理");

  // 4. 取得訂位資訊 (發送 LINE 通知用)
  // 抓取整列資料 (抓寬一點，假設有 12 欄)
  var rowData = sheet.getRange(lastRow, 1, 1, 12).getValues()[0];
  
  // ⚠️ 欄位對應 (基於 image_1a35c0.png)
  // Index: 0=A, 1=B, 2=C(空), 3=D(名), 4=E(電), 5=F(信), 6=G(日), 7=H(時), 8=I(人)
  var customerName = rowData[3]; // D欄
  var date = rowData[6];         // G欄
  var time = rowData[7];         // H欄
  var pax = rowData[8];          // I欄
  
  // 格式化日期
  var dateStr = "未知日期";
  if (date) {
    dateStr = Utilities.formatDate(new Date(date), "GMT+8", "yyyy/MM/dd");
  }
  
  var msg = "🔔 新訂位通知！\n" + 
            "姓名：" + customerName + "\n" + 
            "時間：" + dateStr + " " + time + "\n" + 
            "人數：" + pax + "\n" +
            "狀態：待處理";
            
  sendLineMessage(msg);
}

// ------------------------------------------------------
// 功能 2：當店家手動更改狀態時 (寄送確認信)
// ⚠️ 注意：必須手動設定「編輯時 (On edit)」觸發器連結此函式
// ------------------------------------------------------
function sendEmailOnEdit(e) {
  // 基本防呆
  if (!e) return;
  
  var range = e.range;
  var currentSheet = range.getSheet();
  var row = range.getRow();
  var col = range.getColumn();
  var val = e.value;

  // 確保只在正確的工作表運作
  // 注意：這裡比較保險是用 ss.getSheetByName("表單回應 1") 取得的物件來比對名稱
  if (currentSheet.getName() !== "表單回應 1" && currentSheet.getName() !== "Form Responses 1") return;

  // 檢查條件：
  // 1. 編輯的是 J 欄 (第 10 欄)
  // 2. 內容變成了 "發送確認信"
  // 3. 不是標題列 (row > 1)
  if (col === 10 && val === "發送確認信" && row > 1) {
    
    // 取得該列資料
    var lastCol = currentSheet.getLastColumn();
    var data = currentSheet.getRange(row, 1, 1, lastCol).getValues()[0];
    
    // ⚠️ 欄位對應 (基於 image_1a35c0.png)
    var bookingId = data[0];       // A欄 (ID) -> index 0
    var customerName = data[3];    // D欄 (姓名) -> index 3
    var customerEmail = data[5];   // F欄 (Email) -> index 5 
    var bookingDateRaw = data[6];  // G欄 (日期) -> index 6
    var bookingTime = data[7];     // H欄 (時間) -> index 7
    var pax = data[8];             // I欄 (人數) -> index 8

    // 格式化日期
    var bookingDate = Utilities.formatDate(new Date(bookingDateRaw), "GMT+8", "yyyy/MM/dd");

    // 產生確認連結
    var confirmLink = WEB_APP_URL + "?action=confirm&id=" + bookingId;
    
    // Email 內容
    var subject = "[Cié Cié Taipei] 訂位保留確認通知";
    var body = 
      "<div style='font-family: sans-serif; color: #333;'>" +
        "<h3>" + customerName + " 您好，</h3>" +
        "<p>感謝您的預約，我們已收到您的訂位申請：</p>" +
        "<ul>" +
          "<li><b>日期：</b>" + bookingDate + "</li>" +
          "<li><b>時間：</b>" + bookingTime + "</li>" +
          "<li><b>人數：</b>" + pax + "</li>" +
        "</ul>" +
        "<p>座位目前為您<b>保留中</b>，請點擊下方按鈕確認您的出席：</p>" +
        "<br>" +
        "<a href='" + confirmLink + "' style='background-color:#BFA46F; color:white; padding:12px 24px; text-decoration:none; border-radius:4px; font-weight:bold;'>確認出席 (Confirm Booking)</a>" +
        "<br><br>" +
        "<p style='font-size: 12px; color: #888;'>若按鈕無法點擊，請複製連結開啟：<br>" + confirmLink + "</p>" +
      "</div>";
               
    try {
      MailApp.sendEmail({
        to: customerEmail,
        subject: subject,
        htmlBody: body
      });
      
      // 🟢 修正點在這裡：改成 ss.toast (ss 是全域變數，代表整個檔案)
      ss.toast("✅ 已寄出確認信給 " + customerName + " (" + customerEmail + ")");
      
    } catch (err) {
      // 🔴 這裡也修正成 ss.toast
      ss.toast("❌ 寄信失敗：" + err.message);
      console.log("寄信錯誤: " + err);
    }
  }
}

// ------------------------------------------------------
// 功能 3：處理客人點擊連結 (Web App)
// ------------------------------------------------------
function doGet(e) {
  if (!e || !e.parameter) return HtmlService.createHtmlOutput("無效的請求");
  
  var action = e.parameter.action;
  var id = e.parameter.id;
  
  if (action == "confirm" && id) {
    return confirmBooking(id);
  } else {
    return HtmlService.createHtmlOutput("<h1>連結無效或參數錯誤</h1>");
  }
}

function confirmBooking(targetId) {
  var data = sheet.getDataRange().getValues();
  var rowIndex = -1;
  
  // 搜尋 Excel 裡的 ID (在 A 欄, index 0)
  for (var i = 1; i < data.length; i++) {
    if (data[i][0] == targetId) {
      rowIndex = i + 1; // 轉成實際列號 (從1開始)
      break;
    }
  }
  
  if (rowIndex > 0) {
    // 1. 更新 J 欄 (第 10 欄) 為 "已確認"
    sheet.getRange(rowIndex, 10).setValue("已確認");
    
    // 2. 把整列變綠色
    sheet.getRange(rowIndex, 1, 1, 10).setBackground("#E6F4EA");
    
    // 3. 取得資訊通知店家 (LINE)
    // 重新讀取該列確保資料最新
    var rowData = sheet.getRange(rowIndex, 1, 1, 12).getValues()[0];
    var name = rowData[3]; // D欄
    var dateRaw = rowData[6]; // G欄
    var dateStr = Utilities.formatDate(new Date(dateRaw), "GMT+8", "MM/dd");
    var timeStr = rowData[7]; // H欄
    
    var confirmMsg = "✅ 訂位成立 (客人已按確認)！\n" +
                     "編號：" + targetId + "\n" +
                     "姓名：" + name + "\n" +
                     "時間：" + dateStr + " " + timeStr;
                     
    sendLineMessage(confirmMsg);
    
    // 4. 回傳網頁給客人
    var html = 
      "<html><head><meta name='viewport' content='width=device-width, initial-scale=1'></head>" +
      "<body style='text-align:center; font-family: sans-serif; padding: 40px 20px; background-color: #f9f9f9;'>" +
        "<div style='background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 400px; margin: 0 auto;'>" +
          "<h1 style='color:#4CAF50;'>訂位確認成功！</h1>" +
          "<p>感謝您，Cié Cié Taipei 期待您的光臨。</p>" +
        "</div>" +
      "</body></html>";
    return HtmlService.createHtmlOutput(html).setTitle("訂位確認成功");
    
  } else {
    return HtmlService.createHtmlOutput("<h1>找不到此訂位，可能已被刪除或過期。</h1>");
  }
}

// ------------------------------------------------------
// 工具：發送 LINE Message (Broadcast)
// ------------------------------------------------------
function sendLineMessage(msg) {
  var url = "https://api.line.me/v2/bot/message/broadcast";
  
  var payload = {
    "messages": [
      {
        "type": "text",
        "text": msg
      }
    ]
  };
  
  var options = {
    "method": "post",
    "headers": {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + CHANNEL_ACCESS_TOKEN
    },
    "payload": JSON.stringify(payload),
    "muteHttpExceptions": true
  };
  
  try {
    UrlFetchApp.fetch(url, options);
  } catch (e) {
    Logger.log("LINE Error: " + e.toString());
  }
}
</div>
