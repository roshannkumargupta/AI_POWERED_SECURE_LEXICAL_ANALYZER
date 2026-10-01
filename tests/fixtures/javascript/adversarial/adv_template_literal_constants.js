async function fetchRoles() {
    const query = `SELECT * FROM roles WHERE status = ${'ACTIVE'}`;
    return query;
}
