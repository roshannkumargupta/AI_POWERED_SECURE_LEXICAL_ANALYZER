async function proxyFetch(req, res) {
    const url = req.query.url;
    const resp = await fetch(url);
    res.send(await resp.text());
}
