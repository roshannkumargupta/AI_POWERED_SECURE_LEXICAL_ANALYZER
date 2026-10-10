package com.app.plugin;

public class PluginFactory {
    public static Object instantiate(String className) throws Exception {
        return Class.forName(className).getDeclaredConstructor().newInstance();
    }
}
