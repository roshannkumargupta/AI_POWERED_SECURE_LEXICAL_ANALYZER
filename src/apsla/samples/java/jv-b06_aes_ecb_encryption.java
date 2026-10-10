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
class SampleB06 {
  void handle(HttpServletRequest request, HttpServletResponse response) throws Exception {
    String baseDir = "data/";
    Connection connection = null;
    Socket socket = new Socket();
    Cipher cipher = Cipher.getInstance("AES/ECB/PKCS5Padding");
  }
}
