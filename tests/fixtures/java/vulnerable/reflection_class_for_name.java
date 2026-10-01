import javax.servlet.http.HttpServletRequest;

public class PluginLoader {
    public Class<?> load(HttpServletRequest req) throws Exception {
        String className = req.getParameter("plugin");
        return Class.forName(className);
    }
}
