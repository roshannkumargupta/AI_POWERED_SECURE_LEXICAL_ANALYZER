#include <stdlib.h>
void* safe_allocate_buffer(size_t count, size_t elem_size) {
    return calloc(count, elem_size);
}
