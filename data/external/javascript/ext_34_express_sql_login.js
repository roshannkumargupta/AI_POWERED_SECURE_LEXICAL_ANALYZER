async function loginUser(client, req) {
    const { user, pass } = req.body;
    const sql = `SELECT * FROM accounts WHERE user = '${user}' AND pass = '${pass}'`;
    return await client.query(sql);
}
