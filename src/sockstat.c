#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include "common.h"

char *tcp_max_orphans_file_name = "/proc/sys/net/ipv4/tcp_max_orphans";
char *sockstat_file_name = "/proc/net/sockstat";
char *tcp_mem_file_name = "/proc/sys/net/ipv4/tcp_mem";
char *udp_mem_file_name = "/proc/sys/net/ipv4/udp_mem";

FILE *tcp_max_orphans_file;
FILE *sockstat_file;
FILE *tcp_mem_file;
FILE *udp_mem_file;

int output_mode = 1; // 1 = json; 2 == infofile 

void usage()
{
    printf("usage: sockstat [-i]\n");
    printf("\t-i\toutput stats as key=value instead of JSON\n");
    printf("\t-h\tshow this help message\n");
    exit(EXIT_SUCCESS);
}

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
    
    // check that all files that we need are readable
    if ( access(tcp_max_orphans_file_name, R_OK) == -1){
        die("Cannot access tcp_max_orphans_file");
    }
    if ( access(sockstat_file_name, R_OK) == -1){
        die("Cannot access sockstat_file");
    }
    if ( access(tcp_mem_file_name, R_OK) == -1){
        die("Cannot access tcp_mem_file");
    }
    if ( access(udp_mem_file_name, R_OK) == -1){
        die("Cannot access udp_mem_file");
    }
    
    // define everything we intend to find out
    int tcp_mem_low_threshold; // pages, up to this number, kernel does not care
    int tcp_mem_memory_pressure; // pages, memory pressure mode sets in
    int tcp_mem_max; // pages, out of sockets memory will happen here

    int udp_mem_low_threshold; //pages
    int udp_mem_memory_pressure; //pages
    int udp_mem_max; //pages

    int sockets_used; // total sockets used ( not clear what this includes )

    int tcp_max_orphans; // TCP sockets that are not attached to any file handle
    int tcp_orphan; // TCP orphans count

    int tcp_inuse; // TCP established connections
    int tcp_time_wait; // TCP connections in TIME-WAIT status
    int tcp_alloc; // All TCP sockets (in any state)
    int tcp_mem; // number of pages allocated to TCP (1 page == 4K bytes)

    int udp_inuse; // udp sockets
    int udp_mem; // pages, udp memory

    int udplite_inuse; // udplite sockets RFC3828

    int raw_inuse; // raw sockets (man 7 raw)

    int frag_inuse; // fragments in use
    int frag_mem; // memory used for fragments

    // TODO: have to accept json vs infofile args
    // TODO: has to support outputting as JSON or infofile
    // TODO: option to output in bytes instead of pages
    // TODO: consider also using /proc/net/netstat
   
    int scan_ret; // variable for fscanf return values

    /*
     * Read all the files one by one, line by line.
     * Use fscanf to parse lines.
     */

    // read and parse tcp_max_orphans file
    tcp_max_orphans_file = fopen(tcp_max_orphans_file_name, "r");
    scan_ret = fscanf(tcp_max_orphans_file, "%i", &tcp_max_orphans);
    if (scan_ret != 1){
        die("Failed to read tcp_max_orphans");
    }
    
    // read and parse tcp_mem file
    tcp_mem_file = fopen(tcp_mem_file_name, "r");
    scan_ret = fscanf(tcp_mem_file, "%i %i %i", &tcp_mem_low_threshold, &tcp_mem_memory_pressure, &tcp_mem_max);
    if (scan_ret != 3){
        die("Failed to read tcp_mem_file");
    }

    // read and parse udp_mem file
    udp_mem_file = fopen(udp_mem_file_name, "r");
    scan_ret = fscanf(udp_mem_file, "%i %i %i", &udp_mem_low_threshold, &udp_mem_memory_pressure, &udp_mem_max);
    if (scan_ret != 3){
        die("Failed to read udp_mem_file");
    }
    
    // read and parse sockstat file
    sockstat_file = fopen(sockstat_file_name, "r");
    // example line: sockets: used 140
    scan_ret = fscanf(sockstat_file, "%*s %*s %i", &sockets_used);
    if (scan_ret != 1){
        printf("Scan ret: %d\n",scan_ret);
        die("Failed to read 'sockets used' from sockstat_file");
    }
   
    // example line: TCP: inuse 7 orphan 0 tw 0 alloc 7 mem 3
    scan_ret = fscanf(sockstat_file, "%*s %*s %i %*s %i %*s %i %*s %i %*s %i", &tcp_inuse, &tcp_orphan, &tcp_time_wait, &tcp_alloc, &tcp_mem);
    if (scan_ret != 5){
        printf("Scan ret: %d\n",scan_ret);
        die("Failed to read 'tcp stats' from sockstat_file");
    }
    
    // example line: UDP: inuse 4 mem 1
    scan_ret = fscanf(sockstat_file, "%*s %*s %i %*s %i", &udp_inuse, &udp_mem);
    if (scan_ret != 2){
        printf("Scan ret: %d\n",scan_ret);
        die("Failed to read 'udp stats' from sockstat_file");
    }

    // example line: UDPLITE: inuse 0 
    scan_ret = fscanf(sockstat_file, "%*s %*s %i", &udplite_inuse);
    if (scan_ret != 1){
        printf("Scan ret: %d\n",scan_ret);
        die("Failed to read 'udplite stats' from sockstat_file");
    }

    // example line: RAW: inuse 0
    scan_ret = fscanf(sockstat_file, "%*s %*s %i", &raw_inuse);
    if (scan_ret != 1){
        printf("Scan ret: %d\n",scan_ret);
        die("Failed to read 'raw stats' from sockstat_file");
    }

    // example line: FRAG: inuse 0 memory 0
    scan_ret = fscanf(sockstat_file, "%*s %*s %i %*s %i", &frag_inuse, &frag_mem);
    if (scan_ret != 2){
        printf("Scan ret: %d\n",scan_ret);
        die("Failed to read 'frag stats' from sockstat_file");
    }

    // print out a nice JSON
    int metrics_count = 19;
    struct Metrics metrics[metrics_count];

    metrics[0].name = "tcp.mem_low_threshold";
    metrics[0].value = tcp_mem_low_threshold;

    metrics[1].name = "tcp.mem_memory_pressure";
    metrics[1].value = tcp_mem_memory_pressure;

    metrics[2].name = "tcp.mem_max";
    metrics[2].value = tcp_mem_max;

    metrics[3].name = "udp.mem_low_threshold";
    metrics[3].value = udp_mem_low_threshold;
    
    metrics[4].name = "udp.mem_memory_pressure";
    metrics[4].value = udp_mem_memory_pressure;
    
    metrics[5].name = "udp.mem_max";
    metrics[5].value = udp_mem_max;
    
    metrics[6].name = "sockets.used";
    metrics[6].value = sockets_used;

    metrics[7].name = "tcp.max_orphans";
    metrics[7].value = tcp_max_orphans;

    metrics[8].name = "tcp.orphans";
    metrics[8].value = tcp_orphan;

    metrics[9].name = "tcp.sockets_in_use";
    metrics[9].value = tcp_inuse;

    metrics[10].name = "tcp.time_wait";
    metrics[10].value = tcp_time_wait;
    
    metrics[11].name = "tcp.alloc";
    metrics[11].value = tcp_alloc;

    metrics[12].name = "tcp.mem";
    metrics[12].value = tcp_mem;

    metrics[13].name = "udp.sockets_in_use";
    metrics[13].value = udp_inuse;

    metrics[14].name = "udp.mem";
    metrics[14].value = udp_mem;

    metrics[15].name = "udplite.sockets_in_use";
    metrics[15].value = udplite_inuse;

    metrics[16].name = "raw.sockets_in_use";
    metrics[16].value = raw_inuse;

    metrics[17].name = "frag.in_use";
    metrics[17].value = frag_inuse;

    metrics[18].name = "frag.mem";
    metrics[18].value = frag_mem;

    if ( output_mode == 1){
        jsonprint(metrics_count, metrics);
    } else if ( output_mode == 2) {
        infoprint(metrics_count, metrics);
    }
    exit(0);
}

