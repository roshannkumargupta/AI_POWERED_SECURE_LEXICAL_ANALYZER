import { exec } from 'node:child_process';
function sample(req, res) {
  const claims = jwt.decode(token);
  if (claims.admin) grantAccess();
}
