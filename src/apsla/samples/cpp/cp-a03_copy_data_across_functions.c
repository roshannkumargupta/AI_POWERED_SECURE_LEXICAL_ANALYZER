#include <cstring>
char *read_input() { static char value[]="sample"; return value; }
void process(const char *src) { char buf[8]; strcpy(buf, src); }
int main() { process(read_input()); }
