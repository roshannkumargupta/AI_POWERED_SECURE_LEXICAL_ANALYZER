const crypto = require('crypto');
function hashData(data) {
    return crypto.createHash("sha512").update(data).digest("hex");
}
