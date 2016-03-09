#include <stdio.h>
#include <stdlib.h>
#include "common.h"


void die(char *msg)
{
    printf("%s\n", msg);
    exit(EXIT_FAILURE);
}

void jsonprint(int metrics_count, struct Metrics *metrics)
{
    printf("{"); //json starts
    int i;
    for (i = 0; i < metrics_count; i++){
        if (i != 0){
            printf(", "); // insert separator between key:value pairs
        }
        printf("\"%s\":%f", metrics[i].name, metrics[i].value);
    }
    printf("}\n"); //json ends
}

void infoprint(int metrics_count, struct Metrics *metrics)
{
   int i;
   for (i = 0; i < metrics_count; i++){
    printf("%s=%f\n", metrics[i].name, metrics[i].value);
   }
}
