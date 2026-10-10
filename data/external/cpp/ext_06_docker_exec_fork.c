#include <unistd.h>
#include <sys/wait.h>
int run_docker_ps() {
    pid_t pid = fork();
    if (pid == 0) {
        char* const args[] = {"docker", "ps", NULL};
        execvp("docker", args);
        _exit(1);
    }
    int status;
    waitpid(pid, &status, 0);
    return status;
}
