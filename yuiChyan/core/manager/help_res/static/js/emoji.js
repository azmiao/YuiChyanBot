window.addEventListener('load', () => {
    document.body.addEventListener('click', (e) => {
        const x = e.pageX;
        const y = e.pageY;
        const span = document.createElement('span');

        span.innerHTML = "⭐";
        span.className = 'text';
        span.style.position = 'absolute';
        span.style.top = `${y}px`;
        span.style.left = `${x}px`;
        span.style.opacity = '1';

        // 添加点击穿透和防止选择属性
        span.style.pointerEvents = 'none';
        span.style.userSelect = 'none';

        document.body.appendChild(span);

        let i = 0;
        const animate = () => {
            span.style.top = `${y - i}px`;
            span.style.opacity = `${1 - i / 100}`;
            i++;
            if (i < 100) {
                requestAnimationFrame(animate);
            } else {
                span.remove();
            }
        };
        requestAnimationFrame(animate);
    });
});