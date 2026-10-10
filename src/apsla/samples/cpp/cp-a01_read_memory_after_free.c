#include <cstdlib>
int main(void) { int *p=(int*)malloc(sizeof(int)); *p=7; free(p); return *p; }
