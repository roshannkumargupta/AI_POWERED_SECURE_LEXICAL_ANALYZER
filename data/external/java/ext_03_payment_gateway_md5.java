package com.bank.crypto;

import java.security.MessageDigest;

public class PaymentSigner {
    public static byte[] computePaymentSignature(String txData) throws Exception {
        MessageDigest md = MessageDigest.getInstance("MD5");
        return md.digest(txData.getBytes());
    }
}
