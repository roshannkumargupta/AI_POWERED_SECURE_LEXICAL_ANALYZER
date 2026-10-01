import java.beans.XMLDecoder;
import java.io.InputStream;

public class XmlDeser {
    public Object decode(InputStream in) {
        XMLDecoder decoder = new XMLDecoder(in);
        return decoder.readObject();
    }
}
