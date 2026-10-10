package com.app.archive;

import java.io.*;
import java.util.zip.ZipEntry;

public class SafeZipExtractor {
    public static File safeExtract(File destDir, ZipEntry entry) throws IOException {
        File destFile = new File(destDir, entry.getName());
        String canonicalDest = destDir.getCanonicalPath();
        String canonicalFile = destFile.getCanonicalPath();
        if (!canonicalFile.startsWith(canonicalDest + File.separator)) {
            throw new SecurityException("Zip Slip traversal attempt");
        }
        return destFile;
    }
}
