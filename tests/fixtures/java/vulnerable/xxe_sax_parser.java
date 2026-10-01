import javax.xml.parsers.SAXParserFactory;
import java.io.InputStream;

public class SaxTool {
    public void parseSax(InputStream in) throws Exception {
        SAXParserFactory factory = SAXParserFactory.newInstance();
        factory.newSAXParser().parse(in, new org.xml.sax.helpers.DefaultHandler());
    }
}
