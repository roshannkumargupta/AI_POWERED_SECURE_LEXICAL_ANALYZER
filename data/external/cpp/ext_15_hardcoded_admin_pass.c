const char* ADMIN_PASSWORD = "SuperSecretMasterPass2026!";
int verify_pass(const char* p) {
    extern int strcmp(const char*, const char*);
    return strcmp(p, ADMIN_PASSWORD) == 0;
}
