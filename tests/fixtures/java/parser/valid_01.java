package com.example.service;
import java.util.List;
import java.util.ArrayList;

public class UserService {
    private String domain;

    public UserService(String domain) {
        this.domain = domain;
    }

    public List<String> getUserNames(int limit) {
        List<String> list = new ArrayList<>();
        list.add("alice");
        return list;
    }
}
