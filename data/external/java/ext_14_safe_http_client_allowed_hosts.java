package com.app.net;

import java.net.URI;
import java.util.Set;

public class SafeHttpClient {
    private static final Set<String> ALLOWED = Set.of("api.trusted.com", "auth.trusted.com");

    public static boolean isUrlAllowed(String urlStr) {
        URI uri = URI.create(urlStr);
        return "https".equalsIgnoreCase(uri.getScheme()) && ALLOWED.contains(uri.getHost());
    }
}
