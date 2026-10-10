#include <stdlib.h>
#include <string.h>
int main(int argc, char **argv) { char buf[32]; int n=argc>2 ? atoi(argv[2]) : 0; if (argc>1) memcpy(buf, argv[1], n); return 0; }
