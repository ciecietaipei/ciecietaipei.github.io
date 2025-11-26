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
  var tel = rowData[3];          // 電話
  
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
            "電話：" + tel + "\n" +
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
    var name = rowData[2]; // D欄
    
    var dateRaw = rowData[5]; // G欄
    var dateStr = Utilities.formatDate(new Date(dateRaw), "GMT+8", "MM/dd");
    
    // ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
    // 修正開始：這裡原本直接抓 rowData[6] 會變成 1899 年
    // 請改用下面這段邏輯來處理時間
    var timeRaw = rowData[6]; // H欄
    var timeStr = "";
    if (timeRaw) {
      if (typeof timeRaw === 'object') {
        // 如果是日期物件，就只取出 HH:mm，這樣就不會顯示 1899 年了
        timeStr = Utilities.formatDate(new Date(timeRaw), "GMT+8", "HH:mm");
      } else {
        // 如果已經是字串 (例如 '19:30') 就直接用
        timeStr = timeRaw.toString();
      }
    }
    // 修正結束
    // ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

    var tel = rowData[3];          // 電話

    var confirmMsg = "✅ 訂位成立 (客人已按確認)！\n" +
                     "編號：" + targetId + "\n" +
                     "姓名：" + name + "\n" +
                     "電話：" + tel + "\n" +
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










































/**
 * =========================================================
 * 餐廳訂位系統 - 雙通道結構 (Customer Channel A / Admin Channel B)
 * =========================================================
 */

// ▼▼▼ 設定區：請填入你的兩個通道 Token ▼▼▼
// ⚠️ 通道 B: 管理者/通知帳號的 Token (Web App 的 Webhook 也應該設在這裡)
// const ADMIN_CHANNEL_TOKEN = '請填入_Bot_B_老闆通知用的_Token'; 
const ADMIN_CHANNEL_TOKEN = '';


// ⚠️ 通道 A: 顧客訂位官方帳號的 Token (用於推播給顧客)
// const CUSTOMER_CHANNEL_TOKEN = '請填入_Bot_A_原本舊帳號的_Token';
const CUSTOMER_CHANNEL_TOKEN = '';

// ⚠️ 管理者 User ID (接收通知的老闆 ID)
// const ADMIN_USER_ID = '請填入_老闆你的_User_ID'; 
const ADMIN_USER_ID = '';
// ▲▲▲ 設定結束 ▲▲▲

// ---------------------------------------------------------
// 主函式 (不變)
// ---------------------------------------------------------

function doPost(e) {
  console.error("🔥 收到訊號了！參數 e: " + JSON.stringify(e));

  let postData;
  try {
    postData = JSON.parse(e.postData.contents);
    console.log("Log 2: 收到資料: " + JSON.stringify(postData)); 
  } catch (err) {
    console.log("JSON 解析失敗: " + err.toString());
    return ContentService.createTextOutput("JSON Error");
  }

  if (postData.type === 'new_booking') {
    console.log("Log 3: 進入 new_booking 流程 (LIFF)"); 
    return handleNewBooking(postData);
  } 
  
  else if (postData.events && postData.events.length > 0) {
    console.log("Log 3: 進入 LINE Webhook 事件流程 (按鈕)");
    postData.events.forEach(function(event) {
      if (event.type === 'postback') { 
        // ⚠️ Webhook 來自 Admin Channel B，所以使用 Admin Token
        handlePostback(ADMIN_CHANNEL_TOKEN, event); 
      }
    });
  }
  
  return ContentService.createTextOutput(JSON.stringify({status: 'success'})).setMimeType(ContentService.MimeType.JSON);
}

// ---------------------------------------------------------
// 流程函式：處理新訂位 (使用 Admin Channel B Token 推播給 Admin)
// ---------------------------------------------------------

function handleNewBooking(data) {
  try {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    sheet.appendRow([
      new Date(), data.name, data.phone, data.email, 
      data.date, data.time, data.people, data.note, 
      data.userId, '待確認', '未發送'
    ]);
    console.log("Log 4: Sheet 寫入成功！"); 
    
    const flexContent = createAdminFlex(data, sheet.getLastRow());
    // ⚠️ 推播給 Admin (用 Admin Channel B Token)
    pushFlex(ADMIN_CHANNEL_TOKEN, ADMIN_USER_ID, "新訂位通知", flexContent); 
    
    return ContentService.createTextOutput(JSON.stringify({ status: 'success' })).setMimeType(ContentService.MimeType.JSON);
  } catch (e) {
    console.log("Log 5: 寫入或發送失敗: " + e.toString()); 
    return ContentService.createTextOutput(JSON.stringify({ status: 'error', message: e.toString() })).setMimeType(ContentService.MimeType.JSON);
  }
}

// ---------------------------------------------------------
// 流程函式：處理按鈕回傳 (重點修改處)
// ---------------------------------------------------------

function handlePostback(adminToken, event) {
  const data = JSON.parse(event.postback.data);
  const rowIndex = data.row;
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  
  // 🔍 除錯點 1：確認讀取的是哪一列？
  debugLog("開始處理按鈕回傳，目標列號：" + rowIndex + "，動作：" + data.action);

  // 讀取顧客 ID (請確認您的 Sheet 裡，UserID 真的是在第 9 欄 (I欄) 嗎？)
  const customerUserId = sheet.getRange(rowIndex, 9).getValue(); 
  
  // 🔍 除錯點 2：確認抓到的 ID 是什麼？
  debugLog("讀取到的顧客 UserID：" + customerUserId);

  if (data.action === 'admin_approve') {
      sheet.getRange(rowIndex, 10).setValue('已確認');
      
      // 1. 回覆 Admin
      pushMessage(adminToken, ADMIN_USER_ID, "✅ 訂單 #" + rowIndex + " 已確認"); 

      // 2. 通知 Customer
      debugLog("準備發送給顧客，使用 Token A (Customer Channel)");
      pushMessage(CUSTOMER_CHANNEL_TOKEN, customerUserId, 
                  "🎉 您的訂位 (訂單 #" + rowIndex + ") 已被餐廳確認！期待您的光臨！");
  }
  
  if (data.action === 'user_confirm_attendance') {
      sheet.getRange(rowIndex, 10).setValue('顧客已二確');
      pushMessage(adminToken, ADMIN_USER_ID, "🔔 顧客已完成出席二次確認 (訂單 #" + rowIndex + ")。");
  }
}

// ---------------------------------------------------------
// 工具函式：Flex Message 推播 (多了一個 token 參數)
// ---------------------------------------------------------

function pushFlex(token, to, alt, contents) {
  console.log("準備發送 Flex 給: " + to + " (Token: " + (token === ADMIN_CHANNEL_TOKEN ? "Admin" : "Customer") + ")");
  try {
    const res = UrlFetchApp.fetch('https://api.line.me/v2/bot/message/push', {
      method: 'post',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
      payload: JSON.stringify({ to: to, messages: [{ type: "flex", altText: alt, contents: contents }] }),
      muteHttpExceptions: true
    });
    console.log("LINE Flex 回應: " + res.getContentText()); 
  } catch (e) {
    console.log("LINE Flex 發送崩潰: " + e.toString());
  }
}

// ---------------------------------------------------------
// 工具函式：文字訊息推播 (多了一個 token 參數)
// ---------------------------------------------------------

// ---------------------------------------------------------
// 工具函式：文字訊息推播 (最終偵錯版)
// ---------------------------------------------------------
// 修改後的推播函式 (會把結果寫回 Sheet)
function pushMessage(token, to, msg) {
  debugLog("正在推播訊息給：" + to);
  
  try {
    const res = UrlFetchApp.fetch('https://api.line.me/v2/bot/message/push', {
      method: 'post',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
      payload: JSON.stringify({ to: to, messages: [{ type: 'text', text: msg }] }),
      muteHttpExceptions: true // 讓它不要直接報錯，這樣我們才能讀取錯誤碼
    });
    
    const responseCode = res.getResponseCode();
    const responseBody = res.getContentText();
    
    // 🔍 除錯點 3：LINE 到底回傳了什麼？
    debugLog("LINE 回應碼：" + responseCode + "，回應內容：" + responseBody);
    
    if (responseCode !== 200) {
      debugLog("❌ 發送失敗！請檢查上面的回應內容");
    }

  } catch (e) {
    debugLog("💥 程式崩潰：" + e.toString());
  }
}

// ---------------------------------------------------------
// 工具函式：建立管理者 Flex 卡片 (不變)
// ---------------------------------------------------------

function createAdminFlex(data, row) {
  return {
    "type": "bubble",
    "body": { 
      "type": "box", "layout": "vertical", "contents": [
        { "type": "text", "text": "🔔 新訂位", "weight": "bold", "size": "xl", "color": "#1DB446" },
        { "type": "text", "text": `${data.name} / ${data.people}位`, "margin": "md" },
        { "type": "text", "text": `${data.date} ${data.time}`, "weight": "bold", "size": "lg" }
    ]},
    "footer": { 
      "type": "box", "layout": "vertical", "contents": [
        { 
          "type": "button", 
          "style": "primary", 
          "color": "#06c755", 
          "action": { 
            "type": "postback", 
            "label": "✅ 確認接單", 
            "data": JSON.stringify({ action: "admin_approve", row: String(row) }) 
          }
        }
    ]}
  };

  // ▼▼▼ 把這段加在程式碼最下面 ▼▼▼
function debugLog(msg) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let sheet = ss.getSheetByName("Debug_Log");
    if (!sheet) {
      sheet = ss.insertSheet("Debug_Log"); // 如果沒有就自動建立
      sheet.appendRow(["時間", "訊息內容"]);
    }
    sheet.appendRow([new Date(), msg]);
  } catch (e) {
    // 如果連寫 Log 都失敗，那就真的沒辦法了
  }
}
// ▲▲▲ 除錯工具結束 ▲▲▲
}