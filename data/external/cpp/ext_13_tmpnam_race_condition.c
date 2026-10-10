#include <stdio.h>
FILE* get_scratch_file() {
    char name[L_tmpnam];
    tmpnam(name);
    return fopen(name, "w+");
}
