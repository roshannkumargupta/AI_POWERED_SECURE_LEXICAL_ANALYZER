const { exec } = require('child_process');
function pingHost(host) {
    exec("ping -c 1 " + host);
}
