CFLAGS=-Wall -O2
#CFLAGS=-Wall -O2

INSTALLDIR=/opt/monitoring


BINDIR=bin
SRCDIR=src

all: $(BINDIR)/sockstat $(BINDIR)/files

debug: CFLAGS += -g
debug: $(BINDIR)/sockstat $(BINDIR)/files


$(BINDIR)/sockstat: $(SRCDIR)/sockstat.c $(SRCDIR)/common.h
	gcc -o $(BINDIR)/sockstat $(SRCDIR)/sockstat.c $(SRCDIR)/common.c $(CFLAGS)

$(BINDIR)/files: $(SRCDIR)/files.c $(SRCDIR)/common.h
	gcc -o $(BINDIR)/files $(SRCDIR)/files.c $(SRCDIR)/common.c $(CFLAGS)

clean:
	rm -rf $(BINDIR)/files
	rm -rf $(BINDIR)/sockstat

install:
	mkdir -p $(INSTALLDIR)/
	cp  bin/files $(INSTALLDIR)/
	cp  bin/sockstat $(INSTALLDIR)/
	cp  scripts/endpoint_check.py $(INSTALLDIR)/
