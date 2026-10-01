import java.security.MessageDigest;

public class HashUtil {
    public byte[] makeHash(byte[] data) throws Exception {
        MessageDigest md = MessageDigest.getInstance("MD5");
        return md.digest(data);
    }
}
