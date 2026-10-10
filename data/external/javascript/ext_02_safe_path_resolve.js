const path = require('path');
const fs = require('fs');
function safeReadReport(req, res) {
    const safeFile = path.basename(req.query.file || 'default.txt');
    const fullPath = path.join('/var/reports', safeFile);
    return fs.readFileSync(fullPath, 'utf-8');
}
