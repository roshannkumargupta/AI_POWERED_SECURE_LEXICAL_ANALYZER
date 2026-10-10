#include <stdlib.h>
#include <stdio.h>
int backup_table(const char* table_name) {
    char cmd[256];
    snprintf(cmd, sizeof(cmd), "mysqldump mydb %s", table_name);
    return system(cmd);
}
