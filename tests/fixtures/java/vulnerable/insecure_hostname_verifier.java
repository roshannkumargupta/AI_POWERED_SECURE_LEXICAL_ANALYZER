import javax.net.ssl.HostnameVerifier;

public class InsecureHost {
    public static void disableHostCheck() {
        HostnameVerifier verifier = (hostname, session) -> true;
    }
}
