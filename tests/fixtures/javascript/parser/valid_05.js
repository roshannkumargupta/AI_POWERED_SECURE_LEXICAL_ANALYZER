function handleLogin(req, res) {
    const { username, password } = req.body;
    if (!username || !password) {
        return res.status(400).send("Missing credentials");
    }
    return res.status(200).send("Welcome");
}
