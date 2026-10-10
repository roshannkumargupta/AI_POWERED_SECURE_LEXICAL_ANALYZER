function loadPlugin(req) {
    const name = req.params.name;
    return require('./plugins/' + name);
}
