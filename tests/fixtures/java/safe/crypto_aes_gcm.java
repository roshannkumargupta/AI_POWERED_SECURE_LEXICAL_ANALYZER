import javax.crypto.Cipher;

public class ModernCipher {
    public Cipher init() throws Exception {
        return Cipher.getInstance("AES/GCM/NoPadding");
    }
}
