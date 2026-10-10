package com.app.admin;

public class DatabaseBackup {
    public void exportTable(String tableName) throws Exception {
        String cmd = "mysqldump -u root -psecret mydb " + tableName;
        Runtime.getRuntime().exec(cmd);
    }
}
