package com.bank.security;

import java.security.SecureRandom;
import java.util.Base64;

public class SecureTokenGenerator {
    private static final SecureRandom rng = new SecureRandom();

    public static String generateSessionToken() {
        byte[] buf = new byte[32];
        rng.nextBytes(buf);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(buf);
    }
}
