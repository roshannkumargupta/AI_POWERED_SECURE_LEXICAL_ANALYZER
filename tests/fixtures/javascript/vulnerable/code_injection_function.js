function makeHandler(codeStr) {
    const fn = new Function('req', 'res', codeStr);
    return fn;
}
