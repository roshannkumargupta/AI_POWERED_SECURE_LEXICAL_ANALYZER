const { spawn } = require('child_process');
function listContainers() {
    return spawn('docker', ['ps', '--format', 'json'], { shell: false });
}
