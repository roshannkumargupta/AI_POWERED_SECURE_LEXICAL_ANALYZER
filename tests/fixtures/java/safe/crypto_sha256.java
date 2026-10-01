import java.security.MessageDigest;

public class ModernHash {
    public byte[] hash(byte[] input) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        return md.digest(input);
    }
}
