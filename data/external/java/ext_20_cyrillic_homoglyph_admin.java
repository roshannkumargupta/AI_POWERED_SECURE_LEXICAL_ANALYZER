package com.app.auth;

public class HomoglyphAdmin {
    public static boolean isPrivileged(String admіn) {
        return admіn != null && admіn.equals("root");
    }
}
