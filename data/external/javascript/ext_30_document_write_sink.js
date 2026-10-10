function emitBanner() {
    const banner = new URLSearchParams(location.search).get('banner');
    document.write('<div>' + banner + '</div>');
}
