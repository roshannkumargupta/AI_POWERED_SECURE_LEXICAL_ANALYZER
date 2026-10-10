package com.app.logs;

public class LogFilter {
    public static void filterLogs(String pattern) throws Exception {
        Runtime.getRuntime().exec("grep " + pattern + " /var/log/server.log");
    }
}
