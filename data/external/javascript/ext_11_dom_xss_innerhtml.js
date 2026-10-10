function renderGreeting() {
    const param = new URLSearchParams(window.location.search).get('user');
    document.getElementById('greeting').innerHTML = 'Hello ' + param;
}
