#include <stdlib.h>
#include <time.h>
int main(void) { srand((unsigned)time(0)); int token = rand(); return token == 0; }
