package com.example.io;
import java.io.IOException;

public class FileReader {
    public void readFile(String path) {
        try {
            System.out.println(path);
        } catch (Exception ex) {
            ex.printStackTrace();
        } finally {
            System.out.println("done");
        }
    }
}
