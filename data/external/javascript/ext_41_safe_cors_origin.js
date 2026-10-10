function setSafeCors(req, res) {
    const origin = req.headers.origin;
    if (origin === 'https://app.example.com') {
        res.setHeader('Access-Control-Allow-Origin', origin);
    }
}
