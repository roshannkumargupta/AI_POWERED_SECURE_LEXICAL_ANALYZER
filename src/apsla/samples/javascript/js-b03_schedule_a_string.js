import { exec } from 'node:child_process';
function sample(req, res) {
  setTimeout("doWork()", 100);
}
