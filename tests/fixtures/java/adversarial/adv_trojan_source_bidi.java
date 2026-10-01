public class TrojanBidi {
    public static boolean checkAccess(String role) {
        boolean access = false;
        /* ‮ } ⁦if (access)⁩ ⁦ begin admin check */
        if ("admin".equals(role)) {
            access = true;
        }
        return access;
    }
}
