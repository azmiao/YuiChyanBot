// 帮助中心与管理页搜索、目录切换及安全文本高亮
function escapeRegExp(value) {
    return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function clearHighlights(root) {
    root.querySelectorAll('mark.search-highlight').forEach(mark => {
        mark.replaceWith(document.createTextNode(mark.textContent));
    });
}

function highlightAcrossTextNodes(root, query) {
    if (!root || !query) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
        acceptNode(node) {
            if (!node.nodeValue.trim() || node.parentElement.closest('script, style, mark')) {
                return NodeFilter.FILTER_REJECT;
            }
            return NodeFilter.FILTER_ACCEPT;
        }
    });
    const nodes = [];
    let fullText = '';
    while (walker.nextNode()) {
        const node = walker.currentNode;
        nodes.push({ node, start: fullText.length, end: fullText.length + node.nodeValue.length });
        fullText += node.nodeValue;
    }
    const pattern = new RegExp(escapeRegExp(query), 'gi');
    const matches = [];
    let match;
    while ((match = pattern.exec(fullText)) !== null) {
        matches.push({ start: match.index, end: match.index + match[0].length });
    }
    matches.reverse().forEach(({ start, end }) => {
        nodes.filter(item => item.end > start && item.start < end).forEach(item => {
            const from = Math.max(start, item.start) - item.start;
            const to = Math.min(end, item.end) - item.start;
            const textNode = item.node;
            if (!textNode.parentNode) return;
            const middle = textNode.splitText(from);
            const tail = middle.splitText(to - from);
            const mark = document.createElement('mark');
            mark.className = 'search-highlight';
            middle.parentNode.insertBefore(mark, middle);
            mark.appendChild(middle);
            item.node = tail;
        });
    });
}

function applyHighlights(root, query) {
    if (!root) return;
    clearHighlights(root);
    highlightAcrossTextNodes(root, query);
}

function search() {
    const input = document.getElementById('searchInput').value.trim();
    const items = document.querySelectorAll('.plugin-nav-item');
    const panels = document.querySelectorAll('.help-document-panel');
    let firstMatch = null;

    panels.forEach(panel => {
        const matched = !input || panel.textContent.toLowerCase().includes(input.toLowerCase()) || panel.dataset.searchText.toLowerCase().includes(input.toLowerCase());
        panel.classList.toggle('search-hidden', !matched);
        if (matched && !firstMatch) firstMatch = panel.id;
    });
    items.forEach(item => {
        const panel = document.getElementById(item.dataset.pluginId);
        item.classList.toggle('search-hidden', !(panel && !panel.classList.contains('search-hidden')));
    });
    if (firstMatch) {
        const activePanel = document.querySelector('.help-document-panel.active');
        if (!activePanel || activePanel.classList.contains('search-hidden')) selectPlugin(firstMatch);
    }
    applyHighlights(document.querySelector('[data-highlight-root="true"]'), input);
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

function searchGroups() {
    const input = document.getElementById('groupSearchInput').value.trim().toLowerCase();
    const items = document.querySelectorAll('.group-nav-item');
    const panels = document.querySelectorAll('.group-document');
    let firstMatch = null;
    panels.forEach(panel => {
        const matched = !input || panel.textContent.toLowerCase().includes(input) || panel.dataset.searchText.toLowerCase().includes(input);
        panel.classList.toggle('search-hidden', !matched);
        if (matched && !firstMatch) firstMatch = panel.id;
    });
    items.forEach(item => {
        const panel = document.getElementById(item.dataset.groupId);
        item.classList.toggle('search-hidden', !(panel && !panel.classList.contains('search-hidden')));
    });
    if (firstMatch) selectGroup(firstMatch);
    applyHighlights(document.querySelector('.manager-layout[data-highlight-root="true"]'), input);
    return false;
}

function selectGroup(groupId) {
    document.querySelectorAll('.group-nav-item').forEach(item => item.classList.toggle('active', item.dataset.groupId === groupId));
    document.querySelectorAll('.group-document').forEach(panel => panel.classList.toggle('active', panel.id === groupId));
}

function resetGroupSearch() {
    document.getElementById('groupSearchInput').value = '';
    searchGroups();
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.plugin-nav-item').forEach(item => item.addEventListener('click', () => selectPlugin(item.dataset.pluginId)));
    document.querySelectorAll('.group-nav-item').forEach(item => item.addEventListener('click', () => selectGroup(item.dataset.groupId)));
    const helpInput = document.getElementById('searchInput');
    if (helpInput && document.querySelector('.help-shell')) helpInput.addEventListener('input', search);
    const groupInput = document.getElementById('groupSearchInput');
    if (groupInput) groupInput.addEventListener('input', searchGroups);
});
