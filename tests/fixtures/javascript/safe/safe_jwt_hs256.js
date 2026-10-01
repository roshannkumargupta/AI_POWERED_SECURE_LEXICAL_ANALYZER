const jwt = require('jsonwebtoken');
function verifyToken(token, secret) {
    return jwt.verify(token, secret, { algorithms: ['HS256'] });
}
