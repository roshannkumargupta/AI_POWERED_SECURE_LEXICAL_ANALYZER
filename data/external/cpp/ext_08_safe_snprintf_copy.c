#include <stdio.h>
void safe_process_packet(const char* raw_packet) {
    char local_buf[64];
    snprintf(local_buf, sizeof(local_buf), "%s", raw_packet);
}
