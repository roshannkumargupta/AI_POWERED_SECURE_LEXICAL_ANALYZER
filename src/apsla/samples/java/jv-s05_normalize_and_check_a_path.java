package demo;
import java.io.*;
import java.nio.file.*;
import java.security.*;
import java.sql.*;
import java.util.*;
import java.util.stream.*;
import javax.crypto.*;
import javax.xml.parsers.*;
class Safe5 {
  String read(String id) throws Exception {
    Path root = Paths.get(base).toAbsolutePath().normalize();
Path target = root.resolve(name).normalize();
if (target.startsWith(root)) { return target.toString(); }
    return id;
  }
}
