#include <stdio.h>

void make_temp() {
    char name[L_tmpnam];
    tmpnam(name);
}
