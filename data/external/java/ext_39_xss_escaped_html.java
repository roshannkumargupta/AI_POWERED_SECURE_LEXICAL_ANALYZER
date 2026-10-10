package com.app.web;

import org.apache.commons.text.StringEscapeUtils;

public class SafeGreetingFormatter {
    public static String formatGreeting(String rawName) {
        return "<h1>Welcome " + StringEscapeUtils.escapeHtml4(rawName) + "</h1>";
    }
}
