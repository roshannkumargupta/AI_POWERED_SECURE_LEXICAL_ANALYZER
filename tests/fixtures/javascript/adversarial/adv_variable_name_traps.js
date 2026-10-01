const options = {
    eval: false,
    exec: 'echo',
    innerHTML: 'hello'
};
function getSetting(key) {
    return options[key];
}
console.log(getSetting('exec'));
