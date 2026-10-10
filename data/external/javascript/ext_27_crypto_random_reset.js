const crypto = require('crypto');
function generateSecureOtp() {
    return crypto.randomInt(100000, 1000000).toString();
}
