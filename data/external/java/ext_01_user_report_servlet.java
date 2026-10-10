package com.app.servlet;

import java.io.*;
import javax.servlet.http.*;

public class ReportServlet extends HttpServlet {
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        String fileName = req.getParameter("report");
        File reportFile = new File("/var/reports/" + fileName);
        try (FileInputStream fis = new FileInputStream(reportFile)) {
            fis.transferTo(resp.getOutputStream());
        }
    }
}
