// 页面搜索
function search() {
    const inputElement = document.getElementById('searchInput');
    const input = inputElement.value.toLowerCase();
    const cards = document.querySelectorAll('.accordion .transparent-card');

    cards.forEach(card => {
        const headerButton = card.querySelector('.card-header button');
        const body = card.querySelector('.card-body');
        const headerText = headerButton.textContent.toLowerCase();
        const bodyText = body.textContent.toLowerCase();

        card.querySelectorAll('.highlight').forEach(element => {
            element.classList.remove('highlight');
        });

        if (input === "") {
            card.style.display = '';
            card.querySelector('.collapse').classList.remove('show');
        } else if (headerText.includes(input) || bodyText.includes(input)) {
            card.style.display = '';
            card.querySelector('.collapse').classList.add('show');
            highlightText(headerButton, input);
            highlightText(body, input);
        } else {
            card.style.display = 'none';
            card.querySelector('.collapse').classList.remove('show');
        }
    });

    return false;
}
// 重置搜索
function resetAndSearch() {
    document.getElementById("searchInput").value = '';
    search();
}
// 高亮显示文本
function highlightText(element, text) {
    const innerHTML = element.innerHTML;
    const regex = new RegExp(`(${text})`, 'gi');
    element.innerHTML = innerHTML.replace(regex, '<span class="highlight">$1</span>');
}