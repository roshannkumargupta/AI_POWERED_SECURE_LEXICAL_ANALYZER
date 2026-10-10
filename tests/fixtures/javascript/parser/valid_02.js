class UserStore {
    constructor(db) {
        this.db = db;
    }

    async findById(id) {
        return await this.db.query("SELECT * FROM users WHERE id = ?", [id]);
    }
}
export default UserStore;
