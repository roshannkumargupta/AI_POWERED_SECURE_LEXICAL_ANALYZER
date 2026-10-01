function redirectUser() {
    const target = location.search.slice(1);
    location.href = target;
}
