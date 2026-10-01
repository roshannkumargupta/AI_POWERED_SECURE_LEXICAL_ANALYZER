import java.io.IOException;
import java.util.List;

public class SafeProcess {
    public void execute(List<String> commands) throws IOException {
        ProcessBuilder pb = new ProcessBuilder(commands);
        pb.start();
    }
}
