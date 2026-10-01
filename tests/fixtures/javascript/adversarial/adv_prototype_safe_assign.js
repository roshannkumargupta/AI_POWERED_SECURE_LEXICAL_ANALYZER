function createSafeDict() {
    const target = Object.create(null);
    return Object.assign(target, { safeKey: 1 });
}
