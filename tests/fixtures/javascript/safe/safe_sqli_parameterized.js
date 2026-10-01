function getUser(id) {
    db.query("SELECT * FROM users WHERE id = ?", [id]);
}
