function getLogLevel(env) {
    switch (env) {
        case 'production':
            return 'error';
        case 'staging':
            return 'warn';
        default:
            return 'debug';
    }
}
