#include <stdio.h>
#include <string.h>
int main(void) { char incoming[64], buffer[16]; int received=0; recv(0, incoming, sizeof incoming, 0); strcpy(buffer, incoming); printf(buffer); return received; }
