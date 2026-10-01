import javax.xml.parsers.DocumentBuilderFactory;
import java.io.InputStream;

public class SafeXml {
    public void parse(InputStream in) throws Exception {
        DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
        dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        dbf.newDocumentBuilder().parse(in);
    }
}
