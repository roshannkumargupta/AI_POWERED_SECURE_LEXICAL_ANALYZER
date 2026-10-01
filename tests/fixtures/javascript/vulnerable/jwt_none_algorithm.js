const jwt = require('jsonwebtoken');
function verifyToken(token) {
    return jwt.verify(token, 'secret', { algorithms: ['none'] });
}
