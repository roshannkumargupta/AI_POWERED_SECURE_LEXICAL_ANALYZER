import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;

public class SqlConcat {
    public void runQuery(Connection conn, String userInput) throws Exception {
        Statement stmt = conn.createStatement();
        ResultSet rs = stmt.executeQuery("SELECT * FROM accounts WHERE name = '" + userInput + "'");
    }
}
