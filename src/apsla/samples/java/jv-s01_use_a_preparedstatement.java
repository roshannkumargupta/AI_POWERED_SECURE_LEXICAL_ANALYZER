package demo;
import java.io.*;
import java.nio.file.*;
import java.security.*;
import java.sql.*;
import java.util.*;
import java.util.stream.*;
import javax.crypto.*;
import javax.xml.parsers.*;
class Safe1 {
  String read(String id) throws Exception {
    PreparedStatement stmt = connection.prepareStatement("SELECT * FROM users WHERE name=?");
stmt.setString(1, name);
stmt.executeQuery();
    return id;
  }
}
