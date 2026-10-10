function evaluateCode(raw) {
    const fn = new Function('return ' + raw);
    return fn();
}
