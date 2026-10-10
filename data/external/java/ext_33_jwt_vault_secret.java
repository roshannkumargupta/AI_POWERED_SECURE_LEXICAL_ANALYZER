package com.app.jwt;

public class SafeJwtConfig {
    public static String getSecret() {
        return System.getenv("JWT_SIGNING_SECRET");
    }
}
