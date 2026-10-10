package com.app.logs;

import java.nio.file.*;
import java.util.List;
import java.util.stream.Collectors;

public class SafeLogFilter {
    public static List<String> grep(Path logPath, String term) throws Exception {
        return Files.lines(logPath).filter(line -> line.contains(term)).limit(100).collect(Collectors.toList());
    }
}
