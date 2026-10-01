const crypto = require('crypto');
function generateId() {
    return crypto.randomUUID();
}
