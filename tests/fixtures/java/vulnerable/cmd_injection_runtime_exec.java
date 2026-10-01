import java.io.IOException;
import javax.servlet.http.HttpServletRequest;

public class NetworkTool {
    public void pingHost(HttpServletRequest req) throws IOException {
        String host = req.getParameter("host");
        String cmd = "ping -c 1 " + host;
        Runtime.getRuntime().exec(cmd);
    }
}
