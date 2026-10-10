const crypto = require('crypto');
function hashSha256(data) {
    return crypto.createHash('sha256').update(data).digest('hex');
}
