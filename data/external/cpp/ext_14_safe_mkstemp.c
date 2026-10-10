#include <stdlib.h>
#include <unistd.h>
int get_safe_scratch_fd() {
    char template_str[] = "/tmp/app_XXXXXX";
    return mkstemp(template_str);
}
