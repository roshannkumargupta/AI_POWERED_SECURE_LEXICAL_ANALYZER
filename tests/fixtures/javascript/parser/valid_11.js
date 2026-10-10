function initApp() {
    const btn = document.getElementById('submit-btn');
    btn.addEventListener('click', (e) => {
        e.preventDefault();
        console.log('Clicked');
    });
}
