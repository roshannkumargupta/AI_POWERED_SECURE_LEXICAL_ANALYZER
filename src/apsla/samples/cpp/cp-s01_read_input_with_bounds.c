#include <stdio.h>
#include <stdlib.h>
int main(void) { char buf[32]; if (fgets(buf, sizeof buf, stdin)) { char *end; long n=strtol(buf, &end, 10); if (end != buf && n >= 0 && n <= 100) printf("%ld\n", n); } }
