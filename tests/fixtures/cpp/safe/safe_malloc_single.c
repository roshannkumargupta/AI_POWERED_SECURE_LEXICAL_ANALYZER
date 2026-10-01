#include <stdlib.h>

void alloc_buf() {
    char *p = (char *)malloc(1024);
    free(p);
}
