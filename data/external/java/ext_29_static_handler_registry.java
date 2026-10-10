package com.app.plugin;

import java.util.Map;
import java.util.function.Supplier;

public class SafePluginRegistry {
    private static final Map<String, Supplier<Object>> REG = Map.of(
        "xml", Object::new,
        "json", Object::new
    );
    public static Object create(String key) {
        return REG.getOrDefault(key, Object::new).get();
    }
}
