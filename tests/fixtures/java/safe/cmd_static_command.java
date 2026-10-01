import java.io.IOException;

public class FixedCmd {
    public void check() throws IOException {
        ProcessBuilder pb = new ProcessBuilder("ping", "-c", "1", "127.0.0.1");
        pb.start();
    }
}
