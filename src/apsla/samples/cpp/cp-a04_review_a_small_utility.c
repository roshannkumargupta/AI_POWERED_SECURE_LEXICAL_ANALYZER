#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
int main(void) {
    char input[64], message[32], command[96], password[24];
    printf("Input: ");
    gets(input);
    sprintf(message, "hello %s", input);
    sprintf(command, "echo %s", input);
    system(command);
    srand((unsigned)time(0));
    int token = rand();
    strcpy(password, "demo-password");
    printf("token=%d password=%s\n", token, password);
    return 0;
}
