#include <string.h>
void safe_append_path(char* dest, size_t dest_sz, const char* component) {
    size_t cur_len = strlen(dest);
    if (cur_len + 1 < dest_sz) {
        strncat(dest, component, dest_sz - cur_len - 1);
    }
}
