function validateInput(str) {
    const re = /^[a-zA-Z0-9_-]+$/;
    return re.test(str);
}
