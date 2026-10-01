import java.io.FileInputStream;
import javax.servlet.http.HttpServletRequest;

public class StreamLoader {
    public FileInputStream open(HttpServletRequest req) throws Exception {
        String path = req.getParameter("path");
        return new FileInputStream("/app/uploads/" + path);
    }
}
