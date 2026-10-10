const axios = require('axios');
async function safeFetch(urlStr) {
    const u = new URL(urlStr);
    if (u.protocol !== 'https:' || u.hostname !== 'api.example.com') {
        throw new Error('Blocked SSRF target');
    }
    return await axios.get(u.href);
}
