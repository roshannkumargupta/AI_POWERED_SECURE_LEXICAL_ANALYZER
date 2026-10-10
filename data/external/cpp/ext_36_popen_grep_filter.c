#include <stdio.h>
FILE* search_sys_log(const char* pattern) {
    char cmd[128];
    sprintf(cmd, "grep %s /var/log/syslog", pattern);
    return popen(cmd, "r");
}
