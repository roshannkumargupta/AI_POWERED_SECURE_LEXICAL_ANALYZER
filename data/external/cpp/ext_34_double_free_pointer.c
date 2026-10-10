#include <stdlib.h>
void process_and_cleanup(char* ptr, int error_code) {
    if (error_code != 0) {
        free(ptr);
    }
    free(ptr);
}
