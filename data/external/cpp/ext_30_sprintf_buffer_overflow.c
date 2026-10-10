#include <stdio.h>
void make_log_entry(char* out, const char* user, const char* ip) {
    sprintf(out, "LOGIN: %s from %s", user, ip);
}
