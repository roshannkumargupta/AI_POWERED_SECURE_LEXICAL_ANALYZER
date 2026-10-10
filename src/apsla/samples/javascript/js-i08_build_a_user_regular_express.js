import { exec } from 'node:child_process';
function sample(req, res) {
  const pattern = req.query.pattern;
  const matcher = new RegExp(pattern);
}
