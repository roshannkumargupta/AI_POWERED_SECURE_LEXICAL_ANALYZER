function matchUser(req) {
    const pattern = req.query.pattern;
    const re = new RegExp(pattern);
    return re.test("sample");
}
