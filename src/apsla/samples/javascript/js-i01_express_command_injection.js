import { exec } from 'node:child_process';
function sample(req, res) {
  const raw = req.query.host;
  const host = raw;
  const command = "ping " + host;
  exec(command);
}
