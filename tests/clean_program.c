#include <stdio.h>
#include <string.h>
#include <stdlib.h>

void safe_function(const char *input) {
    char buffer[256];
    // Safe: using strncpy with size limit
    strncpy(buffer, input, sizeof(buffer) - 1);
    buffer[sizeof(buffer) - 1] = '\0';
    printf("Safe buffer: %s\n", buffer);
}

void another_safe(const char *data) {
    char output[512];
    // Safe: using snprintf instead of sprintf
    snprintf(output, sizeof(output), "User input: %s", data);
    printf("%s\n", output);
}

int main(int argc, char *argv[]) {
    if (argc > 1) {
        safe_function(argv[1]);
        another_safe(argv[1]);
    }
    return 0;
}
