import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;
import javax.servlet.http.HttpServletRequest;

public class SafeIdQuery {
    public void run(HttpServletRequest req, Connection conn) throws Exception {
        String rawId = req.getParameter("id");
        int cleanId = Integer.parseInt(rawId);
        Statement stmt = conn.createStatement();
        ResultSet rs = stmt.executeQuery("SELECT * FROM items WHERE id = " + cleanId);
    }
}
