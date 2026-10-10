import { exec } from 'node:child_process';
function sample(req, res) {
  const host = req.query.host;
  runCmd(host);
  function runCmd(cmd) { exec(cmd); }
}
