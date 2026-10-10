#include <stdlib.h>
#include <stdio.h>
int main(void) { char cmd[128]; const char *user=getenv("USER"); sprintf(cmd, "echo %s", user); system(cmd); }
