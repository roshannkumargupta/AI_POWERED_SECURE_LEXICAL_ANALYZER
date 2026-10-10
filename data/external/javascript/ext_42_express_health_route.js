function healthHandler(req, res) {
    res.json({ status: 'ok', uptime: process.uptime() });
}
