package demo;
import java.io.*;
import java.nio.file.*;
import java.security.*;
import java.sql.*;
import java.util.*;
import java.util.stream.*;
import javax.crypto.*;
import javax.xml.parsers.*;
class Safe2 {
  String read(String id) throws Exception {
    int id = Integer.parseInt(request.getParameter("id"));
Statement stmt = connection.createStatement();
stmt.executeQuery("SELECT * FROM users WHERE id=" + id);
    return id;
  }
}
