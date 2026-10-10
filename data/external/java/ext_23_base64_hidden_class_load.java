package com.app.dynamic;

import java.util.Base64;

public class ObfuscatedLoader {
    public static void executePayload(String b64Name) throws Exception {
        String cls = new String(Base64.getDecoder().decode(b64Name));
        Class.forName(cls).getDeclaredConstructor().newInstance();
    }
}
