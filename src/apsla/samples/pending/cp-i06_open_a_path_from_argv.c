#include <stdio.h>
int main(int argc, char **argv) { if (argc>1) { FILE *f=fopen(argv[1], "r"); if (f) fclose(f); } return 0; }
