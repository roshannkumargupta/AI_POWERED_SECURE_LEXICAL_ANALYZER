function safeAdd(a, b) {
    const numA = Number(a);
    const numB = Number(b);
    if (Number.isNaN(numA) || Number.isNaN(numB)) throw new Error('Invalid numbers');
    return numA + numB;
}
