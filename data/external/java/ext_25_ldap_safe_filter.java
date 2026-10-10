package com.app.ldap;

public class SafeLdapFilter {
    public static String escapeLdapFilter(String input) {
        return input.replace("\\", "\\5c").replace("*", "\\2a").replace("(", "\\28").replace(")", "\\29");
    }
}
