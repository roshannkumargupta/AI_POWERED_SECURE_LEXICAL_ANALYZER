async function findUserSafe(db, username) {
    const query = 'SELECT id, email FROM users WHERE username = $1';
    return await db.query(query, [username]);
}
