import java.net.URL;
import javax.servlet.http.HttpServletRequest;

public class WebHook {
    public void trigger(HttpServletRequest req) throws Exception {
        String callback = req.getParameter("callback");
        new URL(callback).openConnection().connect();
    }
}
