import javax.crypto.Cipher;

public class BlockCipher {
    public Cipher getCipher() throws Exception {
        return Cipher.getInstance("AES/ECB/PKCS5Padding");
    }
}
