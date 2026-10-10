function updateSettings(targetObj, jsonBody) {
    const payload = JSON.parse(jsonBody);
    return Object.assign(targetObj, payload);
}
