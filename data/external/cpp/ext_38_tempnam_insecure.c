#include <stdio.h>
char* make_temp_name() {
    return tempnam("/tmp", "pfx");
}
