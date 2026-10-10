function safeMergeSettings(allowedKeys, source) {
    const out = {};
    for (const k of allowedKeys) {
        if (Object.prototype.hasOwnProperty.call(source, k)) {
            out[k] = source[k];
        }
    }
    return out;
}
