package demo;
import java.io.*;
import java.nio.file.*;
import java.security.*;
import java.sql.*;
import java.util.*;
import java.util.stream.*;
import javax.crypto.*;
import javax.xml.parsers.*;
class Safe3 {
  String read(String id) throws Exception {
    MessageDigest.getInstance("SHA-256");
new SecureRandom().nextBytes(new byte[16]);
Cipher.getInstance("AES/GCM/NoPadding");
new ProcessBuilder("echo", "ready").start();
    return id;
  }
}
