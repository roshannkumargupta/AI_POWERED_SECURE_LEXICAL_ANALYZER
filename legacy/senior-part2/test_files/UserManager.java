package com.example.service;

import java.sql.*;
import java.util.*;

/**
 * Realistic User Manager with SQL Injection vulnerabilities.
 * Used for testing Secure Lexical Analyzer.
 */
public class UserManager {
    private Connection dbConnection;

    public UserManager(Connection conn) {
        this.dbConnection = conn;
    }

    // VULNERABLE: Direct string concatenation in SQL query
    public List<String> getUserNames(String departmentId) {
        List<String> users = new ArrayList<>();
        try {
            Statement stmt = dbConnection.createStatement();
            String sql = "SELECT username FROM staff WHERE dept_id = '" + departmentId + "'";
            ResultSet rs = stmt.executeQuery(sql);
            
            while (rs.next()) {
                users.add(rs.getString("username"));
            }
        } catch (SQLException e) {
            System.err.println("Database error: " + e.getMessage());
        }
        return users;
    }

    // SECURE: Uses PreparedStatement (The AI should see this as Safe)
    public boolean updatePassword(String userId, String newPass) {
        String sql = "UPDATE staff SET password = ? WHERE user_id = ?";
        try (PreparedStatement pstmt = dbConnection.prepareStatement(sql)) {
            pstmt.setString(1, newPass);
            pstmt.setString(2, userId);
            return pstmt.executeUpdate() > 0;
        } catch (SQLException e) {
            return false;
        }
    }
}
