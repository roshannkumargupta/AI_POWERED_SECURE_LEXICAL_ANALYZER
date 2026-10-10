package com.example.model;

public enum Role {
    ADMIN("Administrator"),
    USER("Standard User");

    private final String description;

    Role(String description) {
        this.description = description;
    }

    public String getDescription() {
        return this.description;
    }
}
