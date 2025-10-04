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

const posts = [
  `<iframe src="https://www.facebook.com/plugins/video.php?height=476&href=https%3A%2F%2Fwww.facebook.com%2Freel%2F1469372704313298%2F&show_text=false&width=267&t=0" width="267" height="476" style="border:none;overflow:hidden" scrolling="no" frameborder="0" allowfullscreen="true" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share" allowFullScreen="true"></iframe>`
  `<iframe src="https://www.facebook.com/plugins/video.php?height=476&href=https%3A%2F%2Fwww.facebook.com%2Freel%2F1317857456679057%2F&show_text=false&width=267&t=0" width="267" height="476" style="border:none;overflow:hidden" scrolling="no" frameborder="0" allowfullscreen="true" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share" allowFullScreen="true"></iframe>`
  `<iframe src="https://www.facebook.com/plugins/video.php?height=476&href=https%3A%2F%2Fwww.facebook.com%2Freel%2F828911806255422%2F&show_text=false&width=380&t=0" width="380" height="476" style="border:none;overflow:hidden" scrolling="no" frameborder="0" allowfullscreen="true" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share" allowFullScreen="true"></iframe>`,
  `<blockquote class="instagram-media" data-instgrm-permalink="https://www.instagram.com/reel/DPLpns3E4_N/?utm_source=ig_embed&amp;utm_campaign=loading" data-instgrm-version="14" style="background:#FFF; border:0; border-radius:3px; box-shadow:0 0 1px 0 rgba(0,0,0,0.5),0 1px 10px 0 rgba(0,0,0,0.15); margin: 1px; max-width:540px; min-width:326px; padding:0; width:99.375%; width:-webkit-calc(100% - 2px); width:calc(100% - 2px);"><div style="padding:16px;"><a href="https://www.instagram.com/reel/DPLpns3E4_N/?utm_source=ig_embed&amp;utm_campaign=loading" style="background:#FFFFFF; line-height:0; padding:0 0; text-align:center; text-decoration:none; width:100%;" target="_blank"><div style="display: flex; flex-direction: row; align-items: center;"><div style="background-color: #F4F4F4; border-radius: 50%; flex-grow: 0; height: 40px; margin-right: 14px; width: 40px;"></div><div style="display: flex; flex-direction: column; flex-grow: 1; justify-content: center;"><div style="background-color: #F4F4F4; border-radius: 4px; flex-grow: 0; height: 14px; margin-bottom: 6px; width: 100px;"></div><div style="background-color: #F4F4F4; border-radius: 4px; flex-grow: 0; height: 14px; width: 60px;"></div></div></div><div style="padding: 19% 0;"></div><div style="display:block; height:50px; margin:0 auto 12px; width:50px;"><svg width="50px" height="50px" viewBox="0 0 60 60" version="1.1" xmlns="https://www.w3.org/2000/svg" xmlns:xlink="https://www.w3.org/1999/xlink"><g stroke="none" stroke-width="1" fill="none" fill-rule="evenodd"><g transform="translate(-511.000000, -20.000000)" fill="#000000"><g><path d="M556.869,30.41 C554.814,30.41 553.148,32.076 553.148,34.131 C553.148,36.186 554.814,37.852 556.869,37.852 C558.924,37.852 560.59,36.186 560.59,34.131 C560.59,32.076 558.924,30.41 556.869,30.41 M541,60.657 C535.114,60.657 530.342,55.887 530.342,50 C530.342,44.114 535.114,39.342 541,39.342 C546.887,39.342 551.658,44.114 551.658,50 C551.658,55.887 546.887,60.657 541,60.657 M541,33.886 C532.1,33.886 524.886,41.1 524.886,50 C524.886,58.899 532.1,66.113 541,66.113 C549.9,66.113 557.115,58.899 557.115,50 C557.115,41.1 549.9,33.886 541,33.886 M565.378,62.101 C565.244,65.022 564.756,66.606 564.346,67.663 C563.803,69.06 563.154,70.057 562.106,71.106 C561.058,72.155 560.06,72.803 558.662,73.347 C557.607,73.757 556.021,74.244 553.102,74.378 C549.944,74.521 548.997,74.552 541,74.552 C533.003,74.552 532.056,74.521 528.898,74.378 C525.979,74.244 524.393,73.757 523.338,73.347 C521.94,72.803 520.942,72.155 519.894,71.106 C518.846,70.057 518.197,69.06 517.654,67.663 C517.244,66.606 516.755,65.022 516.623,62.101 C516.479,58.943 516.448,57.996 516.448,50 C516.448,42.003 516.479,41.056 516.623,37.899 C516.755,34.978 517.244,33.391 517.654,32.338 C518.197,30.938 518.846,29.942 519.894,28.894 C520.942,27.846 521.94,27.196 523.338,26.654 C524.393,26.244 525.979,25.756 528.898,25.623 C532.057,25.479 533.004,25.448 541,25.448 C548.997,25.448 549.943,25.479 553.102,25.623 C556.021,25.756 557.607,26.244 558.662,26.654 C560.06,27.196 561.058,27.846 562.106,28.894 C563.154,29.942 563.803,30.938 564.346,32.338 C564.756,33.391 565.244,34.978 565.378,37.899 C565.522,41.056 565.552,42.003 565.552,50 C565.552,57.996 565.522,58.943 565.378,62.101 M570.82,37.631 C570.674,34.438 570.167,32.258 569.425,30.349 C568.659,28.377 567.633,26.702 565.965,25.035 C564.297,23.368 562.623,22.342 560.652,21.575 C558.743,20.834 556.562,20.326 553.369,20.18 C550.169,20.033 549.148,20 541,20 C532.853,20 531.831,20.033 528.631,20.18 C525.438,20.326 523.257,20.834 521.349,21.575 C519.376,22.342 517.703,23.368 516.035,25.035 C514.368,26.702 513.342,28.377 512.574,30.349 C511.834,32.258 511.326,34.438 511.181,37.631 C511.035,40.831 511,41.851 511,50 C511,58.147 511.035,59.17 511.181,62.369 C511.326,65.562 511.834,67.743 512.574,69.651 C513.342,71.625 514.368,73.296 516.035,74.965 C517.703,76.634 519.376,77.658 521.349,78.425 C523.257,79.167 525.438,79.673 528.631,79.82 C531.831,79.965 532.853,80.001 541,80.001 C549.148,80.001 550.169,79.965 553.369,79.82 C556.562,79.673 558.743,79.167 560.652,78.425 C562.623,77.658 564.297,76.634 565.965,74.965 C567.633,73.296 568.659,71.625 569.425,69.651 C570.167,67.743 570.674,65.562 570.82,62.369 C570.966,59.17 571,58.147 571,50 C571,41.851 570.966,40.831 570.82,37.631"></path></g></g></g></svg></div><div style="padding-top: 8px;"><div style="color:#3897f0; font-family:Arial,sans-serif; font-size:14px; font-style:normal; font-weight:550; line-height:18px;">在 Instagram 查看這則貼文</div></div><div style="padding: 12.5% 0;"></div><div style="display: flex; flex-direction: row; margin-bottom: 14px; align-items: center;"><div><div style="background-color: #F4F4F4; border-radius: 50%; height: 12.5px; width: 12.5px; transform: translateX(0px) translateY(7px);"></div><div style="background-color: #F4F4F4; height: 12.5px; transform: rotate(-45deg) translateX(3px) translateY(1px); width: 12.5px; flex-grow: 0; margin-right: 14px; margin-left: 2px;"></div><div style="background-color: #F4F4F4; border-radius: 50%; height: 12.5px; width: 12.5px; transform: translateX(9px) translateY(-18px);"></div></div><div style="margin-left: 8px;"><div style="background-color: #F4F4F4; border-radius: 50%; flex-grow: 0; height: 20px; width: 20px;"></div><div style="width: 0; height: 0; border-top: 2px solid transparent; border-left: 6px solid #f4f4f4; border-bottom: 2px solid transparent; transform: translateX(16px) translateY(-4px) rotate(30deg)"></div></div><div style="margin-left: auto;"><div style="width: 0px; border-top: 8px solid #F4F4F4; border-right: 8px solid transparent; transform: translateY(16px);"></div><div style="background-color: #F4F4F4; flex-grow: 0; height: 12px; width: 16px; transform: translateY(-4px);"></div><div style="width: 0; height: 0; border-top: 8px solid #F4F4F4; border-left: 8px solid transparent; transform: translateY(-4px) translateX(8px);"></div></div></div><div style="display: flex; flex-direction: column; flex-grow: 1; justify-content: center; margin-bottom: 24px;"><div style="background-color: #F4F4F4; border-radius: 4px; flex-grow: 0; height: 14px; margin-bottom: 6px; width: 224px;"></div><div style="background-color: #F4F4F4; border-radius: 4px; flex-grow: 0; height: 14px; width: 144px;"></div></div></a><p style="color:#c9c8cd; font-family:Arial,sans-serif; font-size:14px; line-height:17px; margin-bottom:0; margin-top:8px; overflow:hidden; padding:8px 0 7px; text-align:center; text-overflow:ellipsis; white-space:nowrap;"><a href="https://www.instagram.com/reel/DPLpns3E4_N/?utm_source=ig_embed&amp;utm_campaign=loading" style="color:#c9c8cd; font-family:Arial,sans-serif; font-size:14px; font-style:normal; font-weight:normal; line-height:17px; text-decoration:none;" target="_blank">CieCie Taipei（@ciecietaipei）分享的貼文</a></p></div></blockquote>`
];

function showRandomPostModal() {
  const modal = document.getElementById('post-modal');
  const container = document.getElementById('random-post-container');
  const closeBtn = document.getElementById('close-post');
  const randomIndex = Math.floor(Math.random() * posts.length);
  container.innerHTML = posts[randomIndex];
  
  // 改用 classList，配合 CSS 的 .modal.open 樣式
  modal.classList.add('open');
  
  // 動態載入 Instagram embed script（如果貼文包含 instagram）
  if (posts[randomIndex].includes('instagram')) {
    const script = document.createElement('script');
    script.src = '//www.instagram.com/embed.js';
    script.async = true;
    document.body.appendChild(script);
  }
  
  closeBtn.onclick = () => {
    modal.classList.remove('open');
    container.innerHTML = '';
  };
  
  modal.onclick = (e) => {
    if (e.target === modal) {
      modal.classList.remove('open');
      container.innerHTML = '';
    }
  };
}



// 頁面載入自動呼叫
showRandomPostModal();



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
