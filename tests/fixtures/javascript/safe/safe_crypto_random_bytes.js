const crypto = require('crypto');
function generateKey() {
    return crypto.randomBytes(32).toString('hex');
}
