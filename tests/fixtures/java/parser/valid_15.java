package com.example.db;
import java.sql.Connection;
import java.sql.PreparedStatement;

public class UserDao {
    public void findUser(Connection conn, String id) throws Exception {
        PreparedStatement ps = conn.prepareStatement("SELECT * FROM users WHERE id = ?");
        ps.setString(1, id);
        ps.executeQuery();
    }
}
