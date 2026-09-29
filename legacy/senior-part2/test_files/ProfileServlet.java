package com.example.web;

import javax.servlet.*;
import javax.servlet.http.*;
import java.io.*;

/**
 * Realistic Web Servlet demonstrating XSS vulnerability.
 */
public class ProfileServlet extends HttpServlet {

    // VULNERABLE: Direct rendering of user-provided 'username' in HTML
    protected void doGet(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        String username = request.getParameter("name");
        response.setContentType("text/html");
        PrintWriter out = response.getWriter();
        
        out.println("<html><body>");
        out.println("<h1>User Profile</h1>");
        out.println("<p>Welcome, " + username + "!</p>"); // XSS Vulnerability
        out.println("</body></html>");
    }

    // SECURE: Note to student - you would use an encoding library here
    protected void doPost(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        
        String bio = request.getParameter("bio");
        // In a real fix, use StringEscapeUtils.escapeHtml4(bio)
        System.out.println("Processing bio: " + bio);
    }
}
