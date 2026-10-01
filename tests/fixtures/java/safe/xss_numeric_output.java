import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class CounterServlet {
    public void writeCount(HttpServletRequest req, HttpServletResponse resp) throws Exception {
        int count = Integer.parseInt(req.getParameter("c"));
        resp.getWriter().println("Count: " + count);
    }
}
