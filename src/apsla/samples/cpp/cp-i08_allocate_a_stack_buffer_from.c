#include <alloca.h>
#include <stdlib.h>
int main(int argc, char **argv) { int n=argc>1 ? atoi(argv[1]) : 8; char *buf=alloca(n); return buf[0]; }
