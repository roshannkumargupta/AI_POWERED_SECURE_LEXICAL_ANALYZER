function generateSessionToken() {
    const sessionToken = Math.random().toString(36).substring(2);
    return sessionToken;
}
