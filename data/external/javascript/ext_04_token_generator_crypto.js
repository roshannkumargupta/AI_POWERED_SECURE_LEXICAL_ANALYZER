const crypto = require('crypto');
function generateSessionToken() {
    return crypto.randomBytes(32).toString('hex');
}
