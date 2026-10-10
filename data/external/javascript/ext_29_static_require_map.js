const PLUGINS = {
    auth: require('./plugins/auth'),
    cache: require('./plugins/cache')
};
function getPlugin(name) {
    return PLUGINS[name] || null;
}
