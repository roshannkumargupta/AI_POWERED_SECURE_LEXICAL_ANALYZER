const jwt = require('jsonwebtoken');
const JWT_SECRET = 'my_static_production_secret_token_2026';
function signSession(user) {
    return jwt.sign(user, JWT_SECRET, { expiresIn: '1h' });
}
