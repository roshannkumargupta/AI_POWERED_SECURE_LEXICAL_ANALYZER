const crypto = require('crypto');
function hashSha1(data) {
    return crypto.createHash('sha1').update(data).digest('hex');
}
