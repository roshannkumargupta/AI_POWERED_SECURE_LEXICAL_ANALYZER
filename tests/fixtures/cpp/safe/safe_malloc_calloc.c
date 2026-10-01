#include <stdlib.h>

void alloc_safe(size_t n, size_t sz) {
    void *p = calloc(n, sz);
}
