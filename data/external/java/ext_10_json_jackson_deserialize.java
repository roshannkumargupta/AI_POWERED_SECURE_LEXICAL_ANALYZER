package com.app.auth;

import com.fasterxml.jackson.databind.ObjectMapper;

public class SafeSessionLoader {
    private static final ObjectMapper mapper = new ObjectMapper();

    public static UserProfile parseProfile(String json) throws Exception {
        return mapper.readValue(json, UserProfile.class);
    }
}
