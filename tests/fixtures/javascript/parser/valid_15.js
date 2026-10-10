async function searchUsers(db, term) {
    const query = db.select('*').from('users').where('name', 'like', term);
    return await query.execute();
}
