document.addEventListener('DOMContentLoaded', () => {

    // ----------------------------------------------------
    // 影片彈出視窗 (Modal) 邏輯 (此區塊完全不變)
    // ----------------------------------------------------
    const logoTrigger = document.querySelector('.logo-trigger');
    const videoModal = document.getElementById('video-modal');
    // 【修正關閉按鈕選取範圍】
    const videoCloseBtn = videoModal ? videoModal.querySelector('.close-btn') : null;
    const videoPlayer = document.getElementById('popup-video');

    if (logoTrigger && videoModal && videoCloseBtn && videoPlayer) {
        const closeVideoModal = () => {
            videoModal.classList.remove('open');
            videoPlayer.pause();
            videoPlayer.currentTime = 0;
        };

        logoTrigger.addEventListener('click', (e) => {
            e.preventDefault();
            videoModal.classList.add('open');
            videoPlayer.play();
        });
        videoCloseBtn.addEventListener('click', closeVideoModal);
        videoModal.addEventListener('click', (e) => {
            if (e.target === videoModal) closeVideoModal();
        });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && videoModal.classList.contains('open')) closeVideoModal();
        });
    }

    // ----------------------------------------------------
    // 隨機頁面開啟時彈出FB/IG貼文 (此區塊完全不變)
    // ----------------------------------------------------
    const postModal = document.getElementById('post-modal');
    if (postModal) {
        const posts = [
            `<iframe src="https://www.facebook.com/plugins/video.php?height=476&href=https%3A%2F%2Fwww.facebook.com%2Freel%2F1469372704313298%2F&show_text=false&width=267&t=0" width="267" height="476" style="border:none;overflow:hidden" scrolling="no" frameborder="0" allowfullscreen="true" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share" allowFullScreen="true"></iframe>`,
            `<iframe src="https://www.facebook.com/plugins/video.php?height=476&href=https%3A%2F%2Fwww.facebook.com%2Freel%2F668966349168308%2F&show_text=false&width=267&t=0" width="267" height="476" style="border:none;overflow:hidden" scrolling="no" frameborder="0" allowfullscreen="true" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share" allowFullScreen="true"></iframe>`,
            `<iframe src="https://www.facebook.com/plugins/video.php?height=476&href=https%3A%2F%2Fwww.facebook.com%2Freel%2F1317857456679057%2F&show_text=false&width=267&t=0" width="267" height="476" style="border:none;overflow:hidden" scrolling="no" frameborder="0" allowfullscreen="true" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share" allowFullScreen="true"></iframe>`,
            `<iframe src="https://www.facebook.com/plugins/video.php?height=476&href=https%3A%2F%2Fwww.facebook.com%2Freel%2F828911806255422%2F&show_text=false&width=380&t=0" width="380" height="476" style="border:none;overflow:hidden" scrolling="no" frameborder="0" allowfullscreen="true" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share" allowFullScreen="true"></iframe>`,
            '<iframe src="https://www.instagram.com/p/DPLpns3E4_N/embed" width="100%" height="600" frameborder="0"></iframe>',
            '<iframe src="https://www.instagram.com/p/DPYmQm_E17F/embed" width="100%" height="600" frameborder="0"></iframe>'
        ];
        const container = document.getElementById('random-post-container');
        const closeBtn = document.getElementById('close-post');
        const fbLink = document.querySelector('.hero-social-links a[href*="facebook"]');
        const igLink = document.querySelector('.hero-social-links a[href*="instagram"]');

        const closePostModal = () => {
            postModal.classList.remove('open');
            container.innerHTML = '';
        };

        const showRandomPostModal = (type) => {
            const filteredPosts = posts.filter(post => post.includes(type));
            if (filteredPosts.length > 0) {
                const randomIndex = Math.floor(Math.random() * filteredPosts.length);
                container.innerHTML = filteredPosts[randomIndex];
                postModal.classList.add('open');
                if (type === 'instagram') {
                    const script = document.createElement('script');
                    script.src = '//www.instagram.com/embed.js';
                    script.async = true;
                    document.body.appendChild(script);
                }
            }
        };

        if (fbLink) {
            fbLink.addEventListener('click', (e) => {
                e.preventDefault();
                showRandomPostModal('facebook');
            });
        }
        if (igLink) {
            igLink.addEventListener('click', (e) => {
                e.preventDefault();
                showRandomPostModal('instagram');
            });
        }
        if(closeBtn) closeBtn.onclick = closePostModal;
        postModal.onclick = (e) => {
            if (e.target === postModal) closePostModal();
        };
    }

    // ----------------------------------------------------
    // 【唯一的核心修正】讓所有菜單都能滑動
    // ----------------------------------------------------
    const sliders = document.querySelectorAll('.menu-highlights');
    let isDragging = false; // 將此變數放在迴圈外，讓圖片點擊事件可以讀取

    sliders.forEach(slider => {
        let isDown = false;
        let startX;
        let scrollLeft;
        let scrollInterval;
        let scrollDirection = 1;
        const SCROLL_SPEED = 1;
        const INTERVAL_TIME = 25;
        const TOLERANCE = 2;

        function startAutoScroll() {
            if (scrollInterval) clearInterval(scrollInterval);
            scrollInterval = setInterval(() => {
                if (!slider) return;
                slider.scrollLeft += SCROLL_SPEED * scrollDirection;
                const maxScroll = slider.scrollWidth - slider.clientWidth;
                if (slider.scrollLeft >= maxScroll - TOLERANCE) scrollDirection = -1;
                if (slider.scrollLeft <= 0 + TOLERANCE) scrollDirection = 1;
            }, INTERVAL_TIME);
        }

        function stopAutoScroll() {
            if (scrollInterval) {
                clearInterval(scrollInterval);
                scrollInterval = null;
            }
        }

        startAutoScroll();

        slider.addEventListener('mousedown', (e) => {
            isDown = true;
            isDragging = false;
            slider.classList.add('active-drag');
            startX = e.pageX - slider.offsetLeft;
            scrollLeft = slider.scrollLeft;
            stopAutoScroll();
        });

        slider.addEventListener('mouseleave', () => {
            if (isDown) {
                isDown = false;
                slider.classList.remove('active-drag');
                startAutoScroll();
            }
        });

        slider.addEventListener('mouseup', () => {
            isDown = false;
            slider.classList.remove('active-drag');
            // 延遲啟動，避免拖曳後馬上又觸發圖片點擊
            setTimeout(() => {
                startAutoScroll();
            }, 50);
        });

        slider.addEventListener('mousemove', (e) => {
            if (!isDown) return;
            e.preventDefault();
            const walk = e.pageX - startX;
            // 只有當拖曳距離大於一個小閾值時，才真正標記為拖曳
            if (Math.abs(walk) > 5) {
                isDragging = true;
            }
            slider.scrollLeft = scrollLeft - walk * 1.5;
            if (walk > 0) scrollDirection = -1;
            else if (walk < 0) scrollDirection = 1;
        });

        slider.addEventListener('touchstart', (e) => {
            isDown = true;
            isDragging = false;
            startX = e.touches[0].pageX - slider.offsetLeft;
            scrollLeft = slider.scrollLeft;
            stopAutoScroll();
        }, { passive: true });

        slider.addEventListener('touchend', () => {
            isDown = false;
            startAutoScroll();
        });

        slider.addEventListener('touchmove', (e) => {
            if (!isDown) return;
            const walk = e.touches[0].pageX - startX;
            if (Math.abs(walk) > 5) {
                isDragging = true;
            }
            slider.scrollLeft = scrollLeft - walk * 1.5;
            if (walk > 0) scrollDirection = -1;
            else if (walk < 0) scrollDirection = 1;
        });
    });

    // ----------------------------------------------------
    // 區塊滾動淡入效果 (此區塊完全不變)
    // ----------------------------------------------------
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

    // ----------------------------------------------------
    // 圖片點擊放大功能 (此區塊完全不變)
    // ----------------------------------------------------
    const imageModal = document.getElementById('image-modal');
    if (imageModal) {
        const modalImage = document.getElementById('modal-image');
        const closeImageModal = document.getElementById('close-image-modal');
        const clickableImages = document.querySelectorAll('.gallery-item img, .menu-card img');
        
        clickableImages.forEach(img => {
            img.addEventListener('click', (e) => {
                if (isDragging) { // 讀取上面迴圈設定的 isDragging 狀態
                    e.preventDefault();
                    return;
                }
                imageModal.classList.add('open');
                modalImage.src = img.src;
                modalImage.alt = img.alt;
            });
        });

        if (closeImageModal) {
            closeImageModal.addEventListener('click', () => {
                imageModal.classList.remove('open');
                modalImage.src = '';
            });
        }

        imageModal.addEventListener('click', (e) => {
            if (e.target === imageModal) {
                imageModal.classList.remove('open');
                modalImage.src = '';
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && imageModal.classList.contains('open')) {
                imageModal.classList.remove('open');
                modalImage.src = '';
            }
        });
    }

    // ----------------------------------------------------
    // 更新頁尾年份 (此區塊完全不變)
    // ----------------------------------------------------
    const yearSpan = document.getElementById('year');
    if(yearSpan){
        yearSpan.textContent = new Date().getFullYear();
    }
});
