package com.app.controller;

import java.util.Map;

public class HealthController {
    public Map<String, Object> checkHealth() {
        return Map.of("status", "UP", "timestamp", System.currentTimeMillis());
    }
}
