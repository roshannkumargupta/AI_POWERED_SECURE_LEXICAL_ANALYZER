public class EscapeAttack {
    public static void test() {
        // Test unicode escape containing Trojan Source RLO
        String x = "\\u202E reversed text";
    }
}
