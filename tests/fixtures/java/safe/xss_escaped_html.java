import org.apache.commons.text.StringEscapeUtils;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class SafeRender {
    public void render(HttpServletRequest req, HttpServletResponse resp) throws Exception {
        String rawName = req.getParameter("name");
        String safeName = StringEscapeUtils.escapeHtml4(rawName);
        resp.getWriter().println("<div>" + safeName + "</div>");
    }
}
