#include <stdlib.h>

void make_file() {
    char template_file[] = "/tmp/tmpXXXXXX";
    int fd = mkstemp(template_file);
}
