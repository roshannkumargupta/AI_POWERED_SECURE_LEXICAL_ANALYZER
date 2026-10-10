#include <stdio.h>
int main(void) { char name[L_tmpnam]; if (tmpnam(name)) puts(name); return 0; }
