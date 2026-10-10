import { exec } from 'node:child_process';
function sample(req, res) {
  axios.get(req.query.url);
}
