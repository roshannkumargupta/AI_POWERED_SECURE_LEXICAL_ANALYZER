const { execSync } = require('child_process');
function extractArchive(tarName) {
    execSync('tar -xzf ' + tarName);
}
