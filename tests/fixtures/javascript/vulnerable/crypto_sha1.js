const crypto = require('crypto');
function hashData(data) {
    return crypto.createHash("sha1").update(data).digest("hex");
}
