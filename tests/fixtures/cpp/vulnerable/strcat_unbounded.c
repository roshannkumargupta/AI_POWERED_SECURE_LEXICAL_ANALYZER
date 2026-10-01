#include <stdio.h>
#include <string.h>

int main(int argc, char *argv[]) {
    char dest[32] = "Hello ";
    char *src = argv[1];
    strcat(dest, src);
    return 0;
}
