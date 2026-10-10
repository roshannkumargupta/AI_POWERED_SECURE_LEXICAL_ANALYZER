const { exec } = require('child_process');
function dumpTable(tableName) {
    exec('mysqldump mydb ' + tableName, (err, stdout) => {
        console.log(stdout);
    });
}
