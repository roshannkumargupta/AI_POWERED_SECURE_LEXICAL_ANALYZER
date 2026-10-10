package com.app.cloud;

public class SafeAwsConfig {
    public static String getSecretKey() {
        return System.getenv("AWS_SECRET_ACCESS_KEY");
    }
}
