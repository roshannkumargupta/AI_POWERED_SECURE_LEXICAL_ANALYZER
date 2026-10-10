package com.app.util;

import java.nio.file.*;

public class SafePathResolver {
    public static Path resolveSafe(String baseDir, String userPath) {
        Path base = Paths.get(baseDir).toAbsolutePath().normalize();
        Path target = base.resolve(userPath).normalize();
        if (!target.startsWith(base)) {
            throw new SecurityException("Access denied: Path traversal detected");
        }
        return target;
    }
}
