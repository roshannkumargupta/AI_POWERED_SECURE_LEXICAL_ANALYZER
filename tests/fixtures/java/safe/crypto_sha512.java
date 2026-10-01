import java.security.MessageDigest;

public class StrongHash {
    public byte[] hash(byte[] input) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-512");
        return md.digest(input);
    }
}
