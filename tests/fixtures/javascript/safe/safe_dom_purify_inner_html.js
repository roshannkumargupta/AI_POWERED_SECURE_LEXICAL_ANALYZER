function renderBio(userBio) {
    const div = document.getElementById('bio');
    div.innerHTML = DOMPurify.sanitize(userBio);
}
