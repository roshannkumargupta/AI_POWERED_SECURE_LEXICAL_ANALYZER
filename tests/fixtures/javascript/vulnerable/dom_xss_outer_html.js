function updateWidget(userBio) {
    const card = document.getElementById('card');
    card.outerHTML = "<div class='card'>" + userBio + "</div>";
}
