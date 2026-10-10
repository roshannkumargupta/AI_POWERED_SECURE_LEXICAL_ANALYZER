const jwt = require('jsonwebtoken');
function signSessionSafe(user) {
    const secret = process.env.JWT_SECRET;
    if (!secret) throw new Error('JWT_SECRET missing');
    return jwt.sign(user, secret, { expiresIn: '1h' });
}
