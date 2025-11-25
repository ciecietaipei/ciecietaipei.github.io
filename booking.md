// ======================================================
// 全域設定區 (請務必修改這三行)
// ======================================================

// 1. LINE Channel Access Token (請填入您的 Token)
const CHANNEL_ACCESS_TOKEN = "";

// 2. Google Sheet ID (請填入您的試算表 ID)
const SHEET_ID = "";

// 3. Web App 網址 (部署後取得的網址，請填入)
const WEB_APP_URL = ""; 



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
  var customerName = rowData[2]; // D欄 (姓名)
  var dateRaw = rowData[5];      // G欄 (日期原始資料)
  var timeRaw = rowData[6];      // H欄 (時間原始資料)
  var pax = rowData[7];          // I欄 (人數)
  
// 1. 格式化日期 (yyyy/MM/dd)
  var dateStr = "";
  if (dateRaw) {
    // 如果讀出來是字串就直接用，如果是物件就格式化
    if (typeof dateRaw === 'object') {
      dateStr = Utilities.formatDate(new Date(dateRaw), "GMT+8", "yyyy/MM/dd");
    } else {
      dateStr = dateRaw.toString().substring(0, 10); // 簡單防呆
    }
  }

// 2. 格式化時間 (HH:mm) -> 這是修正亂碼的關鍵！
  var timeStr = "";
  if (timeRaw) {
    // 檢查是否為時間物件 (通常 Google Form 來的時間會是物件)
    if (typeof timeRaw === 'object') {
      timeStr = Utilities.formatDate(new Date(timeRaw), "GMT+8", "HH:mm");
    } else {
      // 如果已經是字串 (例如 "20:30") 就直接用
      timeStr = timeRaw.toString();
    }
  }
  
  var msg = "🔔 CIECIE Taipei 新訂位通知！\n" + 
            "姓名：" + customerName + "\n" + 
            "時間：" + dateStr + " " + timeStr + "\n" +  // 這裡改用 timeStr
            "人數：" + pax + "\n" +
            "狀態：待處理";
            
  sendLineMessage(msg);
}

// ------------------------------------------------------
// 功能 2：當店家手動更改狀態時 (寄送確認信)
// ⚠️ 注意：必須手動設定「編輯時 (On edit)」觸發器連結此函式
// ------------------------------------------------------
// ------------------------------------------------------
// 終極智慧版：自動辨識標題 (不怕欄位移動)
// ------------------------------------------------------
function sendEmailOnEdit(e) {
  // 0. 安全檢查
  if (!e) {
    console.log("❌ 請勿直接執行，請去試算表改下拉選單。");
    return;
  }

  var range = e.range;
  var currentSheet = range.getSheet();
  var row = range.getRow();
  var col = range.getColumn();
  var val = e.value;
  var sheetName = currentSheet.getName();

  // 1. 檢查分頁 (只要名字包含 "表單" 或 "Form" 都可以)
  if (sheetName.indexOf("表單") === -1 && sheetName.indexOf("Form") === -1) {
    return;
  }

  // 2. 取得第一列所有的標題 (關鍵步驟！)
  var lastCol = currentSheet.getLastColumn();
  var headers = currentSheet.getRange(1, 1, 1, lastCol).getValues()[0];

  // 3. 自動尋找欄位位置 (模糊搜尋，只要標題包含關鍵字就抓)
  var statusIndex = headers.findIndex(h => h.toString().indexOf("訂位狀態") > -1);
  var emailIndex = headers.findIndex(h => h.toString().indexOf("Email") > -1);
  var nameIndex = headers.findIndex(h => h.toString().indexOf("姓名") > -1);
  var idIndex = headers.findIndex(h => h.toString().indexOf("編號") > -1);

  // 如果找不到 Email 或 狀態欄，就報錯
  if (statusIndex === -1 || emailIndex === -1) {
    ss.toast("❌ 程式找不到『訂位狀態』或『Email』欄位，請檢查標題列。");
    return;
  }

  // 4. 檢查是否觸發：編輯的欄位必須是「狀態欄」 且 值為「發送確認信」
  // (statusIndex 是從 0 開始算，但 col 是從 1 開始算，所以要 +1)
  if (col === (statusIndex + 1) && val === "發送確認信" && row > 1) {
    
    // 取得該列資料
    var data = currentSheet.getRange(row, 1, 1, lastCol).getValues()[0];

    // 🎯 關鍵：使用自動找到的 Index 來抓資料，絕對不會錯！
    var bookingId = (idIndex > -1) ? data[idIndex] : "Unknown";
    var customerName = (nameIndex > -1) ? data[nameIndex] : "貴賓";
    var customerEmail = data[emailIndex]; // 這下絕對會抓到 E 欄！

    console.log("準備寄信給：" + customerName + " <" + customerEmail + ">");

    // 檢查 Email 格式
    if (!customerEmail || customerEmail.toString().indexOf("@") === -1) {
      ss.toast("❌ Email 格式錯誤，抓到的資料是：" + customerEmail);
      return;
    }

    // 準備寄信
    var confirmLink = WEB_APP_URL + "?action=confirm&id=" + bookingId;
    var subject = "[Cié Cié Taipei] 訂位保留確認通知";
    var body = "<h3>" + customerName + " 您好，</h3>" +
               "<p>感謝您的預約，座位為您保留中，請點擊下方連結確認出席：</p>" +
               "<br>" +
               "<a href='" + confirmLink + "' style='background-color:#BFA46F; color:white; padding:12px 24px; text-decoration:none; border-radius:4px;'>確認出席</a>";

    try {
      MailApp.sendEmail({to: customerEmail, subject: subject, htmlBody: body});
      ss.toast("✅ 已寄出確認信給 " + customerName);
    } catch (err) {
      ss.toast("❌ 寄信失敗：" + err.message);
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
    // 1. 更新 J 欄 (第 10 欄) 為 "客戶已確認"
    sheet.getRange(rowIndex, 10).setValue("客戶已確認");
    
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








































// ▼▼▼ 設定區 ▼▼▼
const CHANNEL_ACCESS_TOKEN = '';
const ADMIN_USER_ID = ''; // 測試第一次後，去Sheet複製你的ID填回來
// ▲▲▲ 設定結束 ▲▲▲

function doPost(e) {
// ▼▼▼ 加這行，並確保用 console.error (比較顯眼) ▼▼▼
  console.error("🔥 收到訊號了！參數 e: " + JSON.stringify(e));

  let postData;
  try {
    postData = JSON.parse(e.postData.contents);
    console.log("收到資料: " + JSON.stringify(postData)); // Log 2: 印出收到的內容
  } catch (err) {
    console.log("JSON 解析失敗: " + err.toString());
    return ContentService.createTextOutput("JSON Error");
  }

  // 1. LIFF 新訂位
  if (postData.type === 'new_booking') {
    console.log("進入 new_booking 流程"); // Log 3
    return handleNewBooking(postData);
  } 
  
  // 2. 按鈕回傳
  else if (postData.events && postData.events.length > 0) {
    console.log("進入 Button Postback 流程");
    postData.events.forEach(function(event) {
      if (event.type === 'postback') { handlePostback(event); }
    });
  }
  
  return ContentService.createTextOutput(JSON.stringify({status: 'success'})).setMimeType(ContentService.MimeType.JSON);
}

function handleNewBooking(data) {
  try {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    sheet.appendRow([
      new Date(), data.name, data.phone, data.email, 
      data.date, data.time, data.people, data.note, 
      data.userId, '待確認', '未發送'
    ]);
    console.log("Sheet 寫入成功！"); // Log 4
    
    // 強制發送 LINE
    const flexContent = createAdminFlex(data, sheet.getLastRow());
    pushFlex(ADMIN_USER_ID, "新訂位通知", flexContent);
    
    return ContentService.createTextOutput(JSON.stringify({ status: 'success' })).setMimeType(ContentService.MimeType.JSON);
  } catch (e) {
    console.log("寫入或發送失敗: " + e.toString()); // Log 5: 抓出錯誤
    return ContentService.createTextOutput(JSON.stringify({ status: 'error', message: e.toString() })).setMimeType(ContentService.MimeType.JSON);
  }
}

// ... (以下是工具函式，保持不變) ...

function pushFlex(to, alt, contents) {
  console.log("準備發送 LINE 給: " + to);
  try {
    const res = UrlFetchApp.fetch('https://api.line.me/v2/bot/message/push', {
      method: 'post',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + CHANNEL_ACCESS_TOKEN },
      payload: JSON.stringify({ to: to, messages: [{ type: "flex", altText: alt, contents: contents }] }),
      muteHttpExceptions: true
    });
    console.log("LINE 回應: " + res.getContentText());
  } catch (e) {
    console.log("LINE 發送崩潰: " + e.toString());
  }
}

function createAdminFlex(data, row) {
  return {
    "type": "bubble",
    "body": { "type": "box", "layout": "vertical", "contents": [
        { "type": "text", "text": "🔔 新訂位", "weight": "bold", "size": "xl", "color": "#1DB446" },
        { "type": "text", "text": `${data.name} / ${data.people}位`, "margin": "md" },
        { "type": "text", "text": `${data.date} ${data.time}`, "weight": "bold", "size": "lg" }
    ]},
    "footer": { "type": "box", "layout": "vertical", "contents": [
        { "type": "button", "style": "primary", "color": "#06c755", "action": { "type": "postback", "label": "✅ 確認接單", "data": JSON.stringify({ action: "admin_approve", row: row }) }}
    ]}
  };
}

function handlePostback(event) {
  // 簡化版 Postback，確保不報錯
  const data = JSON.parse(event.postback.data);
  const rowIndex = data.row;
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  if (data.action === 'admin_approve') {
     sheet.getRange(rowIndex, 10).setValue('已確認');
     pushMessage(ADMIN_USER_ID, "✅ 訂單 #" + rowIndex + " 已確認");
  }
  if (data.action === 'user_confirm_attendance') {
     sheet.getRange(rowIndex, 10).setValue('顧客已二確');
     pushMessage(ADMIN_USER_ID, "🎉 顧客出席確認 (訂單 #" + rowIndex + ")");
  }
}

function pushMessage(to, msg) {
  UrlFetchApp.fetch('https://api.line.me/v2/bot/message/push', {
    method: 'post',
    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + CHANNEL_ACCESS_TOKEN },
    payload: JSON.stringify({ to: to, messages: [{ type: 'text', text: msg }] }),
    muteHttpExceptions: true
  });
}