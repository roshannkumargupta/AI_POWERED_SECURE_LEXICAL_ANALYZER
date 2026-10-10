async function findUser(db, username) {
    const query = "SELECT * FROM users WHERE username = '" + username + "'";
    return await db.query(query);
}
