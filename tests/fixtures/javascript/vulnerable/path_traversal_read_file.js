const fs = require('fs');
function loadDoc(req, res) {
    const file = req.params.file;
    fs.readFile('/data/' + file, 'utf8', (err, data) => res.send(data));
}
