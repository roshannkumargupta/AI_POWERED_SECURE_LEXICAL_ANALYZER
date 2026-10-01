const fs = require('fs');
const path = require('path');
function loadSafeDoc(req, res) {
    const safeFile = path.basename(req.params.file);
    fs.readFile(path.join('/data', safeFile), 'utf8', (err, data) => res.send(data));
}
