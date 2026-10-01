public record UserAccount(long id, String username, String email) {
    public String display() {
        return username + " (" + email + ")";
    }
}
