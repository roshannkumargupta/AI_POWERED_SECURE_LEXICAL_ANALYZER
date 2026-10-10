const axios = require('axios');
async function fetchProxy(req, res) {
    const url = req.query.target;
    const resp = await axios.get(url);
    res.send(resp.data);
}
