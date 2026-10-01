async function findItem(req) {
    const id = req.query.id;
    const query = `SELECT * FROM items WHERE id = ${id}`;
    await db.query(query);
}
