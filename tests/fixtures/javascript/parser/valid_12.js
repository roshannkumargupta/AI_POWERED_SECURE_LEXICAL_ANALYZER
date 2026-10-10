function formatGreeting(user) {
    const name = user ? user.name : 'Guest';
    return `Hello, ${name}!`;
}
