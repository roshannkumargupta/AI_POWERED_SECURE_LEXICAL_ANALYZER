import com.thoughtworks.xstream.XStream;
import java.io.InputStream;

public class XStreamDeser {
    public Object parse(InputStream in) {
        XStream xstream = new XStream();
        return xstream.fromXML(in);
    }
}
