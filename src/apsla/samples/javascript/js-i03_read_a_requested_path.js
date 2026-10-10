import { exec } from 'node:child_process';
function sample(req, res) {
  fs.readFile("uploads/" + req.query.file, callback);
}
