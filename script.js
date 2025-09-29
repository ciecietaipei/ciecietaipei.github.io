document.addEventListener('DOMContentLoaded', () => {
    // 範例：未來可以加入圖片輪播邏輯
    
    // 範例：滾動視差效果 (Parallax Scroll) - 僅為演示，CSS已實現基本效果
    const hero = document.querySelector('.hero');

    if (hero) {
        window.addEventListener('scroll', () => {
            let offset = window.pageYOffset;
            // 透過捲動調整背景位置 (這會覆蓋 CSS 的 background-attachment: fixed 的效果，可擇一使用)
            // hero.style.backgroundPositionY = offset * 0.5 + 'px'; 
        });
    }

    // 範例：滾動到指定區塊時，增加淡入效果
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

    // 簡單的 CSS Class for fade-in effect:
    /* 在 style.css 中加入:
       .section { opacity: 0; transform: translateY(20px); transition: opacity 1s ease-out, transform 1s ease-out; }
       .section.visible { opacity: 1; transform: translateY(0); }
    */
});