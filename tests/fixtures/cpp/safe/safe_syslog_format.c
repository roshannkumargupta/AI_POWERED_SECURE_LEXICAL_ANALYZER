#include <syslog.h>

void log_info(const char *msg) {
    syslog(LOG_INFO, "%s", msg);
}
