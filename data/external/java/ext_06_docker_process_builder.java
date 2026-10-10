package com.app.ops;

import java.util.*;

public class ContainerManager {
    public static Process listContainers() throws Exception {
        List<String> args = Arrays.asList("docker", "ps", "--format", "json");
        return new ProcessBuilder(args).start();
    }
}
