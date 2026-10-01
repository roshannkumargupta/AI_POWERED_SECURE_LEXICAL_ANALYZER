const { spawn } = require('child_process');
function listFiles() {
    spawn("ls", ["-la"]);
}
