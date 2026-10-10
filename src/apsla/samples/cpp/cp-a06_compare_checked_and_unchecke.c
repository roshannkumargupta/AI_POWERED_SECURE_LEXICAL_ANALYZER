#include <string.h>
void checked(const char *src, size_t len) { char buf[16]; if (len >= sizeof buf) return; memcpy(buf, src, len); }
void unchecked(const char *src) { char buf[16]; strcpy(buf, src); }
int main(void) { checked("ok", 2); unchecked("sample"); }
