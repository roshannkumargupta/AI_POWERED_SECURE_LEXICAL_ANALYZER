#include <stdlib.h>
int main(int argc, char **argv) { int n=argc>1 ? atoi(argv[1]) : 1; int *items=malloc(n * sizeof(int)); free(items); return 0; }
