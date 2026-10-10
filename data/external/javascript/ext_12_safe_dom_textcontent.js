function renderGreetingSafe() {
    const param = new URLSearchParams(window.location.search).get('user') || 'Guest';
    document.getElementById('greeting').textContent = 'Hello ' + param;
}
