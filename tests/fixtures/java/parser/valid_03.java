package com.example.api;

public interface Repository {
    String findById(int id);
    void delete(String id);
}
