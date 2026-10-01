public class VaultConfig {
    public String getApiKey() {
        return System.getenv("API_KEY");
    }
}
