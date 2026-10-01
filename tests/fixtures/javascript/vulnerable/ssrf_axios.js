const axios = require('axios');
function fetchRemote(req, res) {
    const target = req.query.target;
    axios.get("http://" + target);
}
