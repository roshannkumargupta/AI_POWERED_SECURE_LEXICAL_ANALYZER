import { exec } from 'node:child_process';
function sample(req, res) {
  window.location.href = new URLSearchParams(location.search).get("next");
}
