const fs = require('fs');
function readReport(req, res) {
    const target = '/var/reports/' + req.query.file;
    fs.readFile(target, 'utf-8', (err, data) => {
        res.send(data);
    });
}
