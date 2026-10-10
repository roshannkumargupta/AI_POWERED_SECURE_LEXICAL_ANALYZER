async function loginUserSafe(client, req) {
    const { user, pass } = req.body;
    const sql = 'SELECT id, pass_hash FROM accounts WHERE user = $1';
    return await client.query(sql, [user]);
}
