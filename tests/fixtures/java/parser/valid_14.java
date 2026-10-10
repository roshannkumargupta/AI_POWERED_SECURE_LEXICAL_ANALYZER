package com.example.sec;

public class Sanitizer {
    public String cleanHtml(String input) {
        if (input == null) return "";
        return input.replace("<", "&lt;").replace(">", "&gt;");
    }
}
