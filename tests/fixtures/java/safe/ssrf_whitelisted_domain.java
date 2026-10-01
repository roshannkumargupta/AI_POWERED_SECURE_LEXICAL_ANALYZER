import java.net.URL;

public class FixedClient {
    public void fetch() throws Exception {
        URL url = new URL("https://api.internal.service.com/health");
        url.openConnection().connect();
    }
}
