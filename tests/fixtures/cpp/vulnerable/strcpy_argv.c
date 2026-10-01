#include <stdio.h>
#include <string.h>

int main(int argc, char *argv[]) {
    char dest[32];
    char *src = argv[1];
    strcpy(dest, src);
    return 0;
}
