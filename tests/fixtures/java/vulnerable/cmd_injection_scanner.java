import java.io.IOException;
import java.util.Scanner;

public class CliRunner {
    public static void main(String[] args) throws IOException {
        Scanner scanner = new Scanner(System.in);
        String userInput = scanner.nextLine();
        Runtime.getRuntime().exec("echo " + userInput);
    }
}
