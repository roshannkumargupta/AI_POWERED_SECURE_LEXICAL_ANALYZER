const { execFile } = require('child_process');
function pingHost(host) {
    execFile("ping", ["-c", "1", host]);
}
