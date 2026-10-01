import java.nio.file.Path;
import java.nio.file.Paths;
import javax.servlet.http.HttpServletRequest;

public class SafePath {
    public Path getSafeFile(HttpServletRequest req) {
        String input = req.getParameter("file");
        Path base = Paths.get("/var/app/data").toAbsolutePath().normalize();
        Path target = base.resolve(input).normalize();
        if (!target.startsWith(base)) {
            throw new SecurityException("Traversal attempt");
        }
        return target;
    }
}
