import java.security.MessageDigest;

public class ChecksumUtil {
    public byte[] checksum(byte[] data) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-1");
        return md.digest(data);
    }
}
