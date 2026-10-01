#include <stdlib.h>
#include <stdio.h>

void process() {
    char *p = (char *)malloc(32);
    free(p);
    printf("%s\n", p);
}
