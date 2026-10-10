package com.app.dao;

import java.sql.*;

public class SafeUserDao {
    public ResultSet getUser(Connection conn, long userId) throws SQLException {
        String sql = "SELECT id, email FROM users WHERE id = ?";
        PreparedStatement ps = conn.prepareStatement(sql);
        ps.setLong(1, userId);
        return ps.executeQuery();
    }
}
