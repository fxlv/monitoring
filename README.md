# monitoring

[![Build Status](https://travis-ci.org/fxlv/monitoring.svg?branch=master)](https://travis-ci.org/fxlv/monitoring)
[![Code Climate](https://codeclimate.com/github/fxlv/monitoring/badges/gpa.svg)](https://codeclimate.com/github/fxlv/monitoring)

A collection of scripts and programs that gather various system metrics.
Output is JSON (or optionally, key=value).

This can then be consumed by Telegraf or any other stats collector.

Some parts written in C for more speed. This is especially noticeable when
running on slow HW such as a RaspberryPi.
To build, run `make`. Binaries will then be available in `bin` directory.

## Contents
* endpoint_check.py - measure latency of tcp socket opening and response time from server for simple tcp or http requests.
* files - output stats on open files count (as well as max limit)
* sockstat - various stats on tcp and udp sockets, their memory usage etc.


## Build and install
Classical `make & make install` will work and install the monitoring stuff into `/opt/monitoring`
