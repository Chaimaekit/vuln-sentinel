#include <stdio.h>
#include <string.h>
#include <stdlib.h>

void secret_function() {
    printf("Vulnerability reached!\n");
    system("/bin/sh");
}

void vulnerable_input(char *input) {
    char buffer[64];
    strcpy(buffer, input);
    printf("Input: %s\n", buffer);
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: %s <input>\n", argv[0]);
        return 1;
    }
    vulnerable_input(argv[1]);
    return 0;
}
