import java.io.File;
import javax.servlet.http.HttpServletRequest;

public class FileDownloader {
    public File getFile(HttpServletRequest req) {
        String filename = req.getParameter("file");
        return new File("/var/data/" + filename);
    }
}
