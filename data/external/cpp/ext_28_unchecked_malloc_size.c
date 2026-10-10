#include <stdlib.h>
void* allocate_buffer(size_t count, size_t elem_size) {
    return malloc(count * elem_size);
}
