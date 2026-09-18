// 帮助中心搜索与插件切换
function search() {
    const input = document.getElementById('searchInput').value.trim().toLowerCase();
    const items = document.querySelectorAll('.plugin-nav-item');
    const panels = document.querySelectorAll('.help-document-panel');
    let firstMatch = null;

    panels.forEach(panel => {
        const matched = !input || panel.textContent.toLowerCase().includes(input) || panel.dataset.searchText.toLowerCase().includes(input);
        panel.classList.toggle('search-hidden', !matched);
        if (matched && !firstMatch) firstMatch = panel.id;
    });

    items.forEach(item => {
        const panel = document.getElementById(item.dataset.pluginId);
        const matched = panel && !panel.classList.contains('search-hidden');
        item.classList.toggle('search-hidden', !matched);
    });

    if (firstMatch) {
        const activePanel = document.querySelector('.help-document-panel.active');
        if (!activePanel || activePanel.classList.contains('search-hidden')) selectPlugin(firstMatch);
    }
    return false;
}

function selectPlugin(panelId) {
    document.querySelectorAll('.plugin-nav-item').forEach(item => item.classList.toggle('active', item.dataset.pluginId === panelId));
    document.querySelectorAll('.help-document-panel').forEach(panel => panel.classList.toggle('active', panel.id === panelId));
}

function resetAndSearch() {
    document.getElementById('searchInput').value = '';
    search();
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.plugin-nav-item').forEach(item => item.addEventListener('click', () => selectPlugin(item.dataset.pluginId)));
    document.getElementById('searchInput').addEventListener('input', search);
});