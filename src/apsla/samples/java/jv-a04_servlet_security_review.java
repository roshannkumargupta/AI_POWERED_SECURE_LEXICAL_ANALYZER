package demo;
import java.io.*;
import java.net.*;
import java.security.*;
import java.security.cert.*;
import java.sql.*;
import java.util.*;
import javax.crypto.*;
import javax.net.ssl.*;
import javax.script.*;
import javax.servlet.http.*;
import javax.xml.parsers.*;
import java.beans.*;
class SampleA04 {
  void handle(HttpServletRequest request, HttpServletResponse response) throws Exception {
    String baseDir = "data/";
    Connection connection = null;
    Socket socket = new Socket();
    String name = request.getParameter("name");
    Statement stmt = connection.createStatement();
    stmt.executeQuery("SELECT * FROM users WHERE name=" + name);
    response.getWriter().println(request.getParameter("q"));
    String file = request.getParameter("file");
    new FileInputStream(baseDir + file);
    MessageDigest.getInstance("MD5");
    String password = "demo-credential-value-2026";
    DriverManager.getConnection("jdbc:example:mem", "demo", password);
    DocumentBuilderFactory.newInstance().newDocumentBuilder().parse(request.getInputStream());
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
    // inert review context
  }
}
