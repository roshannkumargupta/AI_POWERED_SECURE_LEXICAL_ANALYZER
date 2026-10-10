package com.example.stream;
import java.util.List;

public class StreamDemo {
    public void process(List<String> items) {
        items.forEach(item -> System.out.println(item));
    }
}
