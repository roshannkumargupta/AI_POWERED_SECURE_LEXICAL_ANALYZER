package com.app.ldap;

import javax.naming.directory.DirContext;
import javax.naming.directory.SearchControls;

public class LdapSearchService {
    public void searchUser(DirContext ctx, String username) throws Exception {
        String filter = "(&(objectClass=user)(uid=" + username + "))";
        ctx.search("ou=people,dc=example,dc=com", filter, new SearchControls());
    }
}
