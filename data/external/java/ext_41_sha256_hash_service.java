package com.app.cert;

import java.security.MessageDigest;

public class SafeCertFingerprint {
    public static byte[] getFingerprint(byte[] certDer) throws Exception {
        return MessageDigest.getInstance("SHA-256").digest(certDer);
    }
}
