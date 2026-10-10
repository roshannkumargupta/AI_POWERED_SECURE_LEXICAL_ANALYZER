#include <cstring>
void copy_text(char *dst, size_t cap, const char *src, size_t len) { if (len >= cap) return; memcpy(dst, src, len); dst[len] = '\0'; }
int main() { char buf[16]; copy_text(buf, sizeof buf, "hello", 5); }
