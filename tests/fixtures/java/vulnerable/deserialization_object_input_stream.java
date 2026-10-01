import java.io.InputStream;
import java.io.ObjectInputStream;
import javax.servlet.http.HttpServletRequest;

public class Deserializer {
    public Object readPayload(HttpServletRequest req) throws Exception {
        InputStream in = req.getInputStream();
        ObjectInputStream ois = new ObjectInputStream(in);
        return ois.readObject();
    }
}
