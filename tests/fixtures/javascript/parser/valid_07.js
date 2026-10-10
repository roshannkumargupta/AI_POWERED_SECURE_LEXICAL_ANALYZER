function parsePayload(raw) {
    try {
        return JSON.parse(raw);
    } catch (err) {
        console.error("Parse failed", err);
        return null;
    } finally {
        console.log("Parsing attempted");
    }
}
