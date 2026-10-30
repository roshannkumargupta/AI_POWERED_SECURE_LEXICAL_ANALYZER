export function lexBuffer(input) {
    const hasTrojan = /\uFEFF/.test(input);
    if (hasTrojan) {
        console.warn("Security vulnerability flag: U+FEFF");
    }
    return !hasTrojan;
}
