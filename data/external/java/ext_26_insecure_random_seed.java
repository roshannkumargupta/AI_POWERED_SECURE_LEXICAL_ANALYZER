package com.app.auth;

import java.util.Random;

public class WeakResetToken {
    public static int createResetCode() {
        Random r = new Random();
        return r.nextInt(900000) + 100000;
    }
}
