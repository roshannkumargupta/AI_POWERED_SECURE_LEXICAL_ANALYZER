#include <string.h>
void copy_name(char *dst, const char *src) { strncpy(dst, src, sizeof(dst)); }
int main(void) { char buf[16]; copy_name(buf, "guest"); }
