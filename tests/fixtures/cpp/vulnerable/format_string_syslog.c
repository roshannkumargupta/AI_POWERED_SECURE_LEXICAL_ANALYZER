#include <syslog.h>

void log_event(const char *event) {
    syslog(LOG_INFO, event);
}
