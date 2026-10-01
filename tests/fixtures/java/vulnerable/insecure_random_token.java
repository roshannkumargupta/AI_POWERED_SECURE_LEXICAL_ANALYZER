import java.util.Random;

public class TokenService {
    public String generatePasswordResetToken() {
        Random rand = new Random();
        return "tok_" + rand.nextInt(1000000);
    }
}
