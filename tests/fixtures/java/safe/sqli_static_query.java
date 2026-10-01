import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;

public class StaticQuery {
    public void load(Connection conn) throws Exception {
        Statement stmt = conn.createStatement();
        ResultSet rs = stmt.executeQuery("SELECT id, name FROM categories");
    }
}
