const { spawn } = require('child_process');
function runShell(command) {
    spawn(command, { shell: true });
}
