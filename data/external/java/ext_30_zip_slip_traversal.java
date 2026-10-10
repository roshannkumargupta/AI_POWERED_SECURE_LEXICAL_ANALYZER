package com.app.archive;

import java.io.*;
import java.util.zip.ZipEntry;

public class ZipExtractor {
    public static void extractEntry(File targetDir, ZipEntry entry, InputStream in) throws IOException {
        File dest = new File(targetDir, entry.getName());
        new FileOutputStream(dest).write(in.readAllBytes());
    }
}
