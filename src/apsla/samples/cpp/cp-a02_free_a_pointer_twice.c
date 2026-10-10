#include <cstdlib>
int main(void) { int *p=(int*)malloc(sizeof(int)); free(p); free(p); return 0; }
