import java.security.SecureRandom;

public class TokenGenerator {
    public byte[] makeToken() {
        SecureRandom secRand = new SecureRandom();
        byte[] token = new byte[32];
        secRand.nextBytes(token);
        return token;
    }
}
