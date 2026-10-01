public class StringLiteralSink {
    public void showHelp() {
        String msg = "Execute Statement: stmt.executeQuery(\"SELECT * FROM users WHERE id = '\" + id);";
        System.out.println(msg);
    }
}
