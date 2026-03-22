#include <stdio.h>
#include <string.h>

void vulnerable_function(char *input) {
    char buffer[64];
    strcpy(buffer, input);  // VULNERABLE: No bounds checking
    printf("Buffer: %s\n", buffer);
}

void another_vulnerable(char *data) {
    char stack_array[128];
    gets(stack_array);  // VULNERABLE: gets() without limit
    sprintf(stack_array, "User input: %s", data);
}

int main(int argc, char *argv[]) {
    if (argc > 1) {
        vulnerable_function(argv[1]);
    }
    return 0;
}
