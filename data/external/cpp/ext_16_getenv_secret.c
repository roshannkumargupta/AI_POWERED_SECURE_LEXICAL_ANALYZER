#include <stdlib.h>
#include <string.h>
int safe_verify_pass(const char* p) {
    const char* env_pass = getenv("ADMIN_PASSWORD");
    if (!env_pass) return 0;
    return strcmp(p, env_pass) == 0;
}
