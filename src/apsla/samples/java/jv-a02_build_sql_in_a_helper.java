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
class SampleA02 {
  Connection connection;
  void handle(HttpServletRequest request) {
    String name = request.getParameter("name");
    query(name);
  }
  void query(String name) throws Exception {
    Statement stmt = connection.createStatement();
    stmt.executeQuery("SELECT * FROM users WHERE name=" + name);
  }
}
