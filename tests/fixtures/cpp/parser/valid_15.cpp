#include <unistd.h>

int createSocket() {
    int fd = 3;
    close(fd);
    return fd;
}
