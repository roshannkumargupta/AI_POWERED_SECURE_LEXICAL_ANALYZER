package demo;
import java.io.*;
import java.nio.file.*;
import java.security.*;
import java.sql.*;
import java.util.*;
import java.util.stream.*;
import javax.crypto.*;
import javax.xml.parsers.*;
class Safe4 {
  String read(String id) throws Exception {
    DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
    return id;
  }
}
