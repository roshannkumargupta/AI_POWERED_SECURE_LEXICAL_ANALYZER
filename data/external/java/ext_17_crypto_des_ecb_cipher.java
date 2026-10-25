package com.app.crypto;

import javax.crypto.Cipher;
import javax.crypto.SecretKey;

public class DesEncryption {
    public static Cipher getDesCipher(SecretKey key) throws Exception {
        Cipher c = Cipher.getInstance("DES/ECB/PKCS5Padding");
        c.init(Cipher.ENCRYPT_MODE, key);
        return c;
    }
}
