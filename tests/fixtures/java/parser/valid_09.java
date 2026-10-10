package com.example.builder;

public class QueryBuilder {
    public QueryBuilder select(String cols) {
        return this;
    }

    public QueryBuilder from(String table) {
        return this;
    }

    public String build() {
        return "SELECT * FROM dual";
    }
}
