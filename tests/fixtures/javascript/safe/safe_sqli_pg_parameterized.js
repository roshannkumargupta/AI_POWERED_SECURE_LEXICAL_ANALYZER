function getItem(id) {
    pool.query("SELECT * FROM items WHERE id = $1", [id]);
}
