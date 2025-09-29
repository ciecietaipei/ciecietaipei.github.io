document.addEventListener('DOMContentLoaded', () => {

    // ----------------------------------------------------
    // 新增：影片彈出視窗 (Modal) 邏輯
    // ----------------------------------------------------
    const logoTrigger = document.querySelector('.logo-trigger');
    const modal = document.getElementById('video-modal');
    const closeBtn = document.querySelector('.close-btn');
    const videoPlayer = document.getElementById('popup-video');

    if (logoTrigger && modal && closeBtn && videoPlayer) {
        
        // 1. 開啟 Modal：點擊 Logo 時
        logoTrigger.addEventListener('click', (e) => {
            e.preventDefault(); // 阻止 A 標籤的預設行為 (跳到頂部)
            modal.classList.add('open');
            videoPlayer.play(); // 開始播放影片
        });

        // 2. 關閉 Modal：點擊 X 關閉按鈕時
        closeBtn.addEventListener('click', () => {
            modal.classList.remove('open');
            videoPlayer.pause(); // 暫停影片
            videoPlayer.currentTime = 0; // 影片跳回開頭 (可選)
        });

        // 3. 關閉 Modal：點擊黑色背景時 (視窗外部)
        modal.addEventListener('click', (e) => {
            // 確保點擊的是 modal 本身，而不是 modal-content 內的元素
            if (e.target === modal) {
                modal.classList.remove('open');
                videoPlayer.pause(); 
                videoPlayer.currentTime = 0;
            }
        });
        
        // 4. 關閉 Modal：按下 ESC 鍵時
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal.classList.contains('open')) {
                modal.classList.remove('open');
                videoPlayer.pause(); 
                videoPlayer.currentTime = 0;
            }
        });
    }

    // ----------------------------------------------------
    // 1. 菜單卡片拖曳滑動功能 (實現左右來回循環)
    // ----------------------------------------------------
    const slider = document.querySelector('.menu-highlights');
    let isDown = false;
    let startX;
    let scrollLeft;
    let scrollInterval; // 用於儲存自動滑動的計時器
    let scrollDirection = 1; // 1: 向右滑動, -1: 向左滑動 (新增方向控制變數)

// ---------------------------------
// 自動滑動設定 (新增容錯值)
// ---------------------------------
const SCROLL_SPEED = 1; 
const INTERVAL_TIME = 25; 
const TOLERANCE = 2; // 新增容錯值 (2px)，確保在邊界附近也能觸發換向

function startAutoScroll() {
    // 如果計時器已存在，先清除，避免重複啟動
    if (scrollInterval) clearInterval(scrollInterval);
    
    scrollInterval = setInterval(() => {
        if (!slider) return;

        // 1. 根據方向變數移動捲軸
        slider.scrollLeft += SCROLL_SPEED * scrollDirection;

        // 2. 判斷是否到達邊界並反轉方向
        const maxScroll = slider.scrollWidth - slider.clientWidth;

        // 檢查是否滑到最右邊 (使用容錯值判斷)
        if (slider.scrollLeft >= maxScroll - TOLERANCE) {
            scrollDirection = -1; // 換向：向左滑
        } 
        
        // 檢查是否滑到最左邊 (使用容錯值判斷)
        if (slider.scrollLeft <= 0 + TOLERANCE) {
            scrollDirection = 1; // 換向：向右滑
        }

    }, INTERVAL_TIME);
}

    function stopAutoScroll() {
        if (scrollInterval) {
            clearInterval(scrollInterval);
            scrollInterval = null;
        }
    }


    if (slider) {
        // ---------------------------------
        // 啟用自動滑動
        // ---------------------------------
        startAutoScroll(); 

        // ---------------------------------
        // 【滑鼠拖曳事件】(手動操作時停止自動滑動)
        // ---------------------------------

        // 滑鼠按下事件 (開始拖曳)
        slider.addEventListener('mousedown', (e) => {
            isDown = true;
            slider.classList.add('active-drag');
            startX = e.pageX - slider.offsetLeft;
            scrollLeft = slider.scrollLeft;
            stopAutoScroll(); // 手動拖曳開始時：停止自動滑動
        });

        // 滑鼠離開或放開事件 (停止拖曳)
        slider.addEventListener('mouseleave', () => {
            if (isDown) {
                 isDown = false;
                 slider.classList.remove('active-drag');
                 startAutoScroll(); // 滑鼠離開時：重新啟動自動滑動
            }
        });

        slider.addEventListener('mouseup', () => {
            isDown = false;
            slider.classList.remove('active-drag');
            startAutoScroll(); // 滑鼠放開時：重新啟動自動滑動
        });

        // 滑鼠移動事件 (進行滑動)
        slider.addEventListener('mousemove', (e) => {
            if (!isDown) return; 
            e.preventDefault();
            const x = e.pageX - slider.offsetLeft;
            // 注意：手動拖曳的方向邏輯不變
            const walk = (x - startX) * 1.5; 
            slider.scrollLeft = scrollLeft - walk;
            
            // 手動拖曳後，重設自動滑動的方向
            if (walk > 0) {
                 scrollDirection = -1; // 用戶向右拖動 (視圖向左滑動)，下次自動向左
            } else if (walk < 0) {
                 scrollDirection = 1; // 用戶向左拖動 (視圖向右滑動)，下次自動向右
            }
        });

        // ---------------------------------
        // 【手機觸控支援】
        // ---------------------------------
        slider.addEventListener('touchstart', (e) => {
            isDown = true;
            startX = e.touches[0].pageX - slider.offsetLeft;
            scrollLeft = slider.scrollLeft;
            stopAutoScroll(); // 觸摸開始時：停止自動滑動
        }, { passive: true });
        
        slider.addEventListener('touchend', () => {
            isDown = false;
            startAutoScroll(); // 觸摸結束時：重新啟動自動滑動
        });

        slider.addEventListener('touchmove', (e) => {
            if (!isDown) return;
            const x = e.touches[0].pageX - slider.offsetLeft;
            const walk = (x - startX) * 1.5;
            slider.scrollLeft = scrollLeft - walk;

            // 觸摸後，重設自動滑動的方向
            if (walk > 0) {
                 scrollDirection = -1; 
            } else if (walk < 0) {
                 scrollDirection = 1; 
            }
        });
    }


    // ----------------------------------------------------
    // 2. 區塊滾動淡入效果 (保持不變)
    // ----------------------------------------------------
    const hero = document.querySelector('.hero');
    // 原本的滾動視差範例程式碼可以移除，因為 CSS 已經處理
    // if (hero) { ... } 
    

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.section').forEach(section => {
        observer.observe(section);
    });

    // 提醒：淡入效果的 CSS 仍需在 style.css 中設定
});