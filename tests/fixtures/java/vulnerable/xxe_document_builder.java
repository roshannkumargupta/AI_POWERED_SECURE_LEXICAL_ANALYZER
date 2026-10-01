import javax.xml.parsers.DocumentBuilderFactory;
import java.io.InputStream;

public class XmlParser {
    public void parse(InputStream in) throws Exception {
        DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
        dbf.newDocumentBuilder().parse(in);
    }
}
