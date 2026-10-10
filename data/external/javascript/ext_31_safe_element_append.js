function emitBannerSafe(bannerText) {
    const div = document.createElement('div');
    div.textContent = bannerText;
    document.body.appendChild(div);
}
