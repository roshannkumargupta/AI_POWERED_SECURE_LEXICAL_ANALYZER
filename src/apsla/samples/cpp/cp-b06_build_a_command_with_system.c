#include <stdio.h>
#include <stdlib.h>
int main(void) { char cmd[128]; const char *dir="sample"; sprintf(cmd, "ls %s", dir); system(cmd); return 0; }
