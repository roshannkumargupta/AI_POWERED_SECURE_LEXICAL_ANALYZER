const { execFile } = require('child_process');

function runTool(bin, args) {
    execFile(bin, args, (err, stdout) => {
        if (err) throw err;
        console.log(stdout);
    });
}
