import { exec } from 'node:child_process';
function sample(req, res) {
  const userInput = process.argv[2];
  eval(userInput);
}
