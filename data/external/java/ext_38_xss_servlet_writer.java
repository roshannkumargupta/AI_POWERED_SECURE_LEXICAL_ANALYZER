package com.app.web;

import javax.servlet.http.*;

public class UserGreetingServlet extends HttpServlet {
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws Exception {
        String name = req.getParameter("name");
        resp.getWriter().println("<h1>Welcome " + name + "</h1>");
    }
}
