const hash = location.hash.slice(1);
const output = document.getElementById('output');
output.innerHTML = "Welcome " + hash;
