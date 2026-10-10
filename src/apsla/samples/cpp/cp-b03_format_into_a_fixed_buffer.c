#include <stdio.h>
int main(void) { char buf[16]; const char *a="service", *b="status"; sprintf(buf, "%s-%s", a, b); puts(buf); }
