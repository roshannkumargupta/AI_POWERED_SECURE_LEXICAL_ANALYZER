package com.example.utils;

import java.io.*;

/**
 * System utility service to manage external processes.
 * Contains both vulnerable and secure command execution logic.
 */
public class SystemService {

    // VULNERABLE: Direct string concatenation into shell command
    public void executeRemoteCheck(String hostname) {
        try {
            String command = "ping -c 4 " + hostname;
            Process p = Runtime.getRuntime().exec(command);
            
            BufferedReader reader = new BufferedReader(new InputStreamReader(p.getInputStream()));
            String line;
            while ((line = reader.readLine()) != null) {
                System.out.println(line);
            }
        } catch (IOException e) {
            System.err.println("Execution failed: " + e.getMessage());
        }
    }

    // SECURE: Uses ProcessBuilder to avoid shell injection
    public void secureExecute(String filename) {
        ProcessBuilder pb = new ProcessBuilder("cat", "/var/logs/" + filename);
        try {
            Process p = pb.start();
            // Process output...
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
