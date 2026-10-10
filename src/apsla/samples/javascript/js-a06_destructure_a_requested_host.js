import { exec } from 'node:child_process';
function sample(req, res) {
  const { host } = req.query;
  exec(`ping ${host}`);
}
