package com.example.dispatch;

public class Dispatcher {
    public int dispatch(String cmd) {
        switch (cmd) {
            case "start": return 1;
            case "stop": return 0;
            default: return -1;
        }
    }
}
