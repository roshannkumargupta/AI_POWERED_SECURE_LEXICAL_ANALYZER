package com.app.net;

import java.io.InputStream;
import java.net.URL;

public class WebhookFetcher {
    public InputStream fetchHook(String remoteUrl) throws Exception {
        URL url = new URL(remoteUrl);
        return url.openStream();
    }
}
