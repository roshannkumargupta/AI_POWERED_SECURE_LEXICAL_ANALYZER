import javax.net.ssl.SSLContext;

public class SafeTls {
    public SSLContext getContext() throws Exception {
        return SSLContext.getDefault();
    }
}
