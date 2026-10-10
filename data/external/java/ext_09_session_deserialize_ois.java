package com.app.auth;

import java.io.*;

public class SessionDeserializer {
    public static Object loadSession(InputStream in) throws Exception {
        ObjectInputStream ois = new ObjectInputStream(in);
        return ois.readObject();
    }
}
