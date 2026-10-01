import java.util.Random;

public class GameDice {
    public int rollDice() {
        Random rand = new Random();
        return rand.nextInt(6) + 1;
    }
}
