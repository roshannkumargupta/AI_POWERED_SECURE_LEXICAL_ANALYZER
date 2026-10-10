#include <stdio.h>
void safe_make_log_entry(char* out, size_t out_sz, const char* user, const char* ip) {
    snprintf(out, out_sz, "LOGIN: %s from %s", user, ip);
}
