public class DriverLoader {
    public void load() throws Exception {
        Class.forName("com.mysql.cj.jdbc.Driver");
    }
}
