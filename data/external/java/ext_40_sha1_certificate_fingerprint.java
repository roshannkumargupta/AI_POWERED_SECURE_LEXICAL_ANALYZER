package com.app.cert;

import java.security.MessageDigest;

public class CertFingerprint {
    public static byte[] getFingerprint(byte[] certDer) throws Exception {
        return MessageDigest.getInstance("SHA-1").digest(certDer);
    }
}
