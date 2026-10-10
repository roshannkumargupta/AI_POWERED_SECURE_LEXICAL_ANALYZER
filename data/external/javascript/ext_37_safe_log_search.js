const fs = require('fs');
const readline = require('readline');
async function safeSearchLogs(keyword) {
    const rl = readline.createInterface({ input: fs.createReadStream('/var/log/app.log') });
    const matches = [];
    for await (const line of rl) {
        if (line.includes(keyword)) matches.push(line);
    }
    return matches;
}
