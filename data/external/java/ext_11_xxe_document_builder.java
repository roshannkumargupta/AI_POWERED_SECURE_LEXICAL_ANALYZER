package com.app.xml;

import java.io.InputStream;
import javax.xml.parsers.DocumentBuilderFactory;

public class XmlParserService {
    public void parseFeed(InputStream stream) throws Exception {
        DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
        dbf.newDocumentBuilder().parse(stream);
    }
}
