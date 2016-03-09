#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include "common.h"
//
// /proc/sys/fs/file-nr 
// contains 3 numbers: number of open files, free file handles and max open files limit
//


char *filenr_file_name = "/proc/sys/fs/file-nr";
FILE *filenr_file;

int output_mode = 1; // 1 = json; 2 == infofile 

void usage()
{
    printf("usage: files  [-i]\n");
    printf("\t-i\toutput stats as key=value instead of JSON\n");
    printf("\t-h\tshow this help message\n");
    exit(EXIT_SUCCESS);
}

char *json = "json";


int main(int argc, char *argv[])
{
    int arg;
    while(( arg = getopt(argc, argv, "ih")) != -1 ){
        switch(arg){
            case 'i':
                output_mode = 2;
                break;
            case 'h':
                usage();
                break;
            case '?':
                usage();
                break;
            default:
                usage();
        }
    }


    filenr_file = fopen(filenr_file_name, "r");
    if (filenr_file == NULL) {
        die("Could not open filenr_file");
    }
    int num_open_files, num_free_file_handles, num_max_open_files;
    int scan_ret;
    // we expect the file to contain 3 integers
    scan_ret = fscanf(filenr_file, "%i %i %i", &num_open_files, &num_free_file_handles, &num_max_open_files);
    if(scan_ret != 3){
        die("Unexpected filenr_file content");
    }
    // this is a bit unfelxible, but will do for now
    int metrics_count = 3;
    struct Metrics metrics[metrics_count];

    metrics[0].name = "num_open_files";
    metrics[0].value = num_open_files;

    metrics[1].name = "num_free_file_handles";
    metrics[1].value = num_free_file_handles;

    metrics[2].name = "num_max_open_files";
    metrics[2].value = num_max_open_files;

    if ( output_mode == 1){
        jsonprint(metrics_count, metrics);
    } else if ( output_mode == 2){
        infoprint(metrics_count, metrics);
    }

    return 0;
}
