#include <string.h>
int main(void) { char dst[16]; const char *name = "guest"; strcpy(dst, name); return dst[0]; }
