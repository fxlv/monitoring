#ifndef _common_h
#define _common_h

struct Metrics {
    char *name;
    float value; //float is not always called for here, perhaps needs changing
};
void die(char *msg);
void jsonprint(int metrics_count, struct Metrics *metrics);
void infoprint(int metrics_count, struct Metrics *metrics);

#endif
