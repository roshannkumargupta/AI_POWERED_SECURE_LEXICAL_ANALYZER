const { exec } = require('child_process');
function searchLogs(filter) {
    exec('grep ' + filter + ' /var/log/app.log', (err, stdout) => {
        console.log(stdout);
    });
}
