const crypto = require('crypto');
function verifyPayment(txId, amount) {
    return crypto.createHash('md5').update(txId + ':' + amount).digest('hex');
}
