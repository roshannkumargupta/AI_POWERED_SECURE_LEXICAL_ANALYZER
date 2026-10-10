package com.example.data;
import java.util.Optional;

public class DataStore {
    public Optional<String> query(String key) {
        if (key == null) {
            return Optional.empty();
        }
        return Optional.of(key.toUpperCase());
    }
}
