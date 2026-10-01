#include <stdio.h>

int main(int argc, char *argv[]) {
    char *cmd = argv[1];
    FILE *fp = popen(cmd, "r");
    return 0;
}
