#include <stdio.h>
void safe_read_username() {
    char name_buf[32];
    if (fgets(name_buf, sizeof(name_buf), stdin) != NULL) {
        // Process safely
    }
}
