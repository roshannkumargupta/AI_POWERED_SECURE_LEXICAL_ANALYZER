import javax.crypto.Cipher;

public class LegacyCrypto {
    public Cipher getCipher() throws Exception {
        return Cipher.getInstance("DES");
    }
}
