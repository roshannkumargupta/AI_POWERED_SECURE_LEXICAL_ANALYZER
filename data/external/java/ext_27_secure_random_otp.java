package com.app.auth;

import java.security.SecureRandom;

public class StrongResetToken {
    public static int createOtp() throws Exception {
        return SecureRandom.getInstanceStrong().nextInt(900000) + 100000;
    }
}
