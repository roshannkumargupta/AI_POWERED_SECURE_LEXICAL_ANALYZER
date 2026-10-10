package com.app.ops;

public class ShellRunner {
    public static void runScript(String userCommand) throws Exception {
        new ProcessBuilder("sh", "-c", "echo " + userCommand).start();
    }
}
