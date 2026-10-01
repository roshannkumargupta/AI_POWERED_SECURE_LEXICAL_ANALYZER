import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;
import javax.servlet.http.HttpServletRequest;

public class SqlBuilder {
    public void search(HttpServletRequest req, Connection conn) throws Exception {
        String term = req.getParameter("q");
        StringBuilder sb = new StringBuilder();
        sb.append("SELECT * FROM items WHERE title LIKE '%");
        sb.append(term);
        sb.append("%'");
        Statement stmt = conn.createStatement();
        ResultSet rs = stmt.executeQuery(sb.toString());
    }
}
