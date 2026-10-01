#include <stdio.h>

int main(int argc, char *argv[]) {
    char *path = argv[1];
    FILE *fp = fopen(path, "r");
    return 0;
}
