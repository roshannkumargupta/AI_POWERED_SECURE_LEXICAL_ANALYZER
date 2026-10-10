import { exec } from 'node:child_process';
function sample(req, res) {
  const raw = req.query.id;
  const id = raw;
  db.query(`SELECT * FROM users WHERE id=${id}`);
}
