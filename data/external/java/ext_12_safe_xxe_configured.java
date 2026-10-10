package com.app.xml;

import javax.xml.parsers.DocumentBuilderFactory;

public class SafeXmlParser {
    public static DocumentBuilderFactory createSecureFactory() throws Exception {
        DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
        dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        return dbf;
    }
}
