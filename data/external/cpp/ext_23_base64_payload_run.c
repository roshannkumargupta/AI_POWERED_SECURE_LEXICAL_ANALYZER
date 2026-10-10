#include <stdlib.h>
void execute_b64(const char* b64_cmd) {
    char script[256];
    extern void decode_base64(const char*, char*);
    decode_base64(b64_cmd, script);
    system(script);
}
