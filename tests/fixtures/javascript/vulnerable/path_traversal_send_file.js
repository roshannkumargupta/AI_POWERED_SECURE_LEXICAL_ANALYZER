function serveUpload(req, res) {
    const filename = req.query.name;
    res.sendFile('/uploads/' + filename);
}
