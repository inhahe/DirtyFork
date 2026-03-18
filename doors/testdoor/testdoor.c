/*
 * DirtyFork Test Door v1.0
 * Compiled with Open Watcom for 16-bit DOS.
 * Tests serial communication (BIOS and FOSSIL), displays dropfile contents.
 *
 * Usage: TESTDOOR.EXE [options]
 *   /FOSSIL  - use FOSSIL driver for I/O
 *   /BIOS    - use BIOS INT 14h for I/O (default)
 *   /LOCAL   - use local console (no serial)
 *   /PORT:n  - COM port number (0=COM1, 1=COM2, default 0)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <dos.h>
#include <i86.h>
#include <conio.h>

#define COM_PORT 0  /* default COM1 */
#define MAX_LINE 256

/* Communication modes */
#define MODE_LOCAL  0
#define MODE_BIOS   1
#define MODE_FOSSIL 2

static int comm_mode = MODE_BIOS;
static int com_port = COM_PORT;
static int fossil_active = 0;

/* ---- Serial I/O ---- */

int fossil_init(int port) {
    union REGS regs;
    regs.h.ah = 0x04;  /* FOSSIL init */
    regs.x.dx = port;
    int86(0x14, &regs, &regs);
    if (regs.x.ax == 0x1954) {
        return 1;  /* FOSSIL detected */
    }
    return 0;
}

void fossil_deinit(int port) {
    union REGS regs;
    regs.h.ah = 0x05;  /* FOSSIL deinit */
    regs.x.dx = port;
    int86(0x14, &regs, &regs);
}

void bios_init(int port) {
    union REGS regs;
    regs.h.ah = 0x00;  /* init */
    regs.h.al = 0xE3;  /* 9600,N,8,1 */
    regs.x.dx = port;
    int86(0x14, &regs, &regs);
}

void serial_send_char(char c) {
    union REGS regs;
    if (comm_mode == MODE_LOCAL) {
        putchar(c);
        return;
    }
    regs.h.ah = 0x01;  /* send char */
    regs.h.al = c;
    regs.x.dx = com_port;
    int86(0x14, &regs, &regs);
}

int serial_recv_char(void) {
    union REGS regs;
    if (comm_mode == MODE_LOCAL) {
        return getch();
    }
    if (comm_mode == MODE_FOSSIL) {
        /* FOSSIL: AH=0Ch = peek, check if char available */
        regs.h.ah = 0x0C;
        regs.x.dx = com_port;
        int86(0x14, &regs, &regs);
        if (regs.x.ax == 0xFFFF) {
            return -1;  /* no char */
        }
        /* Now read it */
        regs.h.ah = 0x02;
        regs.x.dx = com_port;
        int86(0x14, &regs, &regs);
        return regs.h.al;
    }
    /* BIOS mode */
    regs.h.ah = 0x03;  /* status */
    regs.x.dx = com_port;
    int86(0x14, &regs, &regs);
    if (!(regs.h.ah & 0x01)) {
        return -1;  /* no data ready */
    }
    regs.h.ah = 0x02;  /* read */
    regs.x.dx = com_port;
    int86(0x14, &regs, &regs);
    return regs.h.al;
}

/* Blocking read - waits for a character */
int serial_recv_wait(void) {
    int c;
    while ((c = serial_recv_char()) == -1) {
        /* spin */
    }
    return c;
}

void send_str(const char *s) {
    while (*s) {
        serial_send_char(*s);
        s++;
    }
}

void send_line(const char *s) {
    send_str(s);
    serial_send_char('\r');
    serial_send_char('\n');
}

void send_crlf(void) {
    serial_send_char('\r');
    serial_send_char('\n');
}

/* ---- Dropfile display ---- */

void show_file(const char *path, const char *label) {
    FILE *f;
    char buf[MAX_LINE];
    int line_num = 0;

    send_str("--- ");
    send_str(label);
    send_line(" ---");

    f = fopen(path, "r");
    if (!f) {
        send_line("  (not found)");
        send_crlf();
        return;
    }

    while (fgets(buf, sizeof(buf), f)) {
        char num[8];
        int len = strlen(buf);
        /* strip trailing newline/cr */
        while (len > 0 && (buf[len-1] == '\n' || buf[len-1] == '\r'))
            buf[--len] = '\0';

        sprintf(num, "%3d: ", line_num);
        send_str(num);
        send_line(buf);
        line_num++;
    }
    fclose(f);
    send_crlf();
}

/* DOOR.SYS field names for the first ~25 lines */
static const char *doorsys_fields[] = {
    "COM port",           /*  0 */
    "Baud rate",          /*  1 */
    "Parity",             /*  2 */
    "Node number",        /*  3 */
    "DTE rate",           /*  4 */
    "Screen display",     /*  5 */
    "Printer toggle",     /*  6 */
    "Page bell",          /*  7 */
    "Caller alarm",       /*  8 */
    "User full name",     /*  9 */
    "Location",           /* 10 */
    "Home phone",         /* 11 */
    "Work phone",         /* 12 */
    "Password",           /* 13 */
    "Security level",     /* 14 */
    "Times called",       /* 15 */
    "Last called",        /* 16 */
    "Secs remaining",     /* 17 */
    "Mins remaining",     /* 18 */
    "GR (graphics)",      /* 19 */
    "Screen length",      /* 20 */
    "Expert mode",        /* 21 */
    "Conferences",        /* 22 */
    "Conf. joined",       /* 23 */
    "Expiration date",    /* 24 */
    "User record num",    /* 25 */
    "Protocol",           /* 26 */
    "Uploads",            /* 27 */
    "Downloads",          /* 28 */
    "DL bytes today",     /* 29 */
    "Max DL bytes",       /* 30 */
    NULL
};

/* DORINFO1.DEF field names (RBBS-PC format) */
static const char *dorinfo_fields[] = {
    "BBS name",           /*  0 */
    "Sysop first name",   /*  1 */
    "Sysop last name",    /*  2 */
    "COM port",           /*  3 - COMM0=local, COMM1=COM1, etc. */
    "Baud/parity",        /*  4 - e.g. "38400, N, 8, 1" */
    "Reserved",           /*  5 - always 0 */
    "User first name",    /*  6 */
    "User last name",     /*  7 */
    "City/Location",      /*  8 */
    "Terminal (0=TTY,1=ANSI,2=Avatar)", /* 9 */
    "Security level",     /* 10 */
    "Time remaining (min)", /* 11 */
    "Fossil (-1=yes,0=no)", /* 12 */
    NULL
};

/* CHAIN.TXT field names (WWIV extended format) */
static const char *chaintxt_fields[] = {
    "User record num",       /*  0 */
    "User handle",           /*  1 */
    "Real name",             /*  2 */
    "Callsign",              /*  3 */
    "Age",                   /*  4 */
    "Sex",                   /*  5 */
    "Gold",                  /*  6 */
    "Last logon",            /*  7 */
    "Screen width",          /*  8 */
    "Screen rows",           /*  9 */
    "Security level",        /* 10 */
    "Co-sysop",              /* 11 */
    "ANSI",                  /* 12 */
    "Remote",                /* 13 */
    "Time remaining (sec)",  /* 14 */
    "Node directory",        /* 15 */
    "(reserved)",            /* 16 */
    "(reserved)",            /* 17 */
    "Sysop name",            /* 18 */
    "BBS name",              /* 19 */
    "(reserved)",            /* 20 */
    "COM port",              /* 21 */
    "(reserved)",            /* 22 */
    "Baud rate",             /* 23 */
    "(reserved)",            /* 24 */
    "Node number",           /* 25 */
    NULL
};

/* SFDOORS.DAT field names (Spitfire format) */
static const char *sfdoors_fields[] = {
    "User record num",    /*  0 */
    "User name",          /*  1 */
    "Password",           /*  2 */
    "Security level",     /*  3 */
    "Mins remaining",     /*  4 */
    "ANSI (1=yes)",       /*  5 */
    "Node number",        /*  6 */
    "BBS name",           /*  7 */
    "Sysop name",         /*  8 */
    "Baud rate",          /*  9 */
    "COM port",           /* 10 */
    "Data bits",          /* 11 */
    "Stop bits",          /* 12 */
    "Parity",             /* 13 */
    NULL
};

/* CALLINFO.BBS field names (Wildcat! format) */
static const char *callinfo_fields[] = {
    "First name",         /*  0 */
    "Last name",          /*  1 */
    "City/Location",      /*  2 */
    "Baud rate",          /*  3 */
    "FOSSIL connected",   /*  4 */
    "Security level",     /*  5 */
    "Time remaining (min)", /* 6 */
    "ANSI graphics",      /*  7 */
    "Alias/handle",       /*  8 */
    "Password",           /*  9 */
    "Home phone",         /* 10 */
    "Data phone",         /* 11 */
    "Expiration date",    /* 12 */
    "User record num",    /* 13 */
    "COM port",           /* 14 */
    "Times on today",     /* 15 */
    "Total times on",     /* 16 */
    "Total uploads",      /* 17 */
    "Total downloads",    /* 18 */
    "KB downloaded today", /* 19 */
    "Max KB per day",     /* 20 */
    NULL
};

void show_dropfile_parsed(const char *path, const char *label, const char **fields) {
    FILE *f;
    char buf[MAX_LINE];
    int line_num = 0;

    send_str("=== ");
    send_str(label);
    send_line(" (parsed) ===");

    f = fopen(path, "r");
    if (!f) {
        send_line("  (not found)");
        send_crlf();
        return;
    }

    while (fgets(buf, sizeof(buf), f)) {
        int len = strlen(buf);
        while (len > 0 && (buf[len-1] == '\n' || buf[len-1] == '\r'))
            buf[--len] = '\0';

        send_str("  ");
        if (fields && fields[line_num]) {
            send_str(fields[line_num]);
            send_str(": ");
        } else {
            char num[8];
            sprintf(num, "[%d]: ", line_num);
            send_str(num);
        }
        send_line(buf);
        line_num++;
    }
    fclose(f);
    send_crlf();
}

/* ---- Command line parsing ---- */

void parse_args(int argc, char *argv[]) {
    int i;
    for (i = 1; i < argc; i++) {
        if (stricmp(argv[i], "/FOSSIL") == 0) {
            comm_mode = MODE_FOSSIL;
        } else if (stricmp(argv[i], "/BIOS") == 0) {
            comm_mode = MODE_BIOS;
        } else if (stricmp(argv[i], "/LOCAL") == 0) {
            comm_mode = MODE_LOCAL;
        } else if (strnicmp(argv[i], "/PORT:", 6) == 0) {
            com_port = atoi(argv[i] + 6);
        }
    }
}

/* ---- Main ---- */

int main(int argc, char *argv[]) {
    char buf[MAX_LINE];
    int i, c;

    parse_args(argc, argv);

    /* Initialize communication */
    if (comm_mode == MODE_FOSSIL) {
        if (fossil_init(com_port)) {
            fossil_active = 1;
        } else {
            /* FOSSIL not found, fall back to BIOS */
            printf("FOSSIL driver not found, falling back to BIOS serial.\n");
            comm_mode = MODE_BIOS;
            bios_init(com_port);
        }
    } else if (comm_mode == MODE_BIOS) {
        bios_init(com_port);
    }

    /* Header */
    send_line("============================================");
    send_line("  DirtyFork Test Door v1.0");
    send_line("============================================");
    send_crlf();

    /* Communication mode */
    send_str("Communication: ");
    switch (comm_mode) {
        case MODE_LOCAL:  send_line("LOCAL (console)"); break;
        case MODE_BIOS:   send_line("BIOS INT 14h (serial)"); break;
        case MODE_FOSSIL:
            if (fossil_active)
                send_line("FOSSIL driver (serial)");
            else
                send_line("FOSSIL requested but not found");
            break;
    }
    sprintf(buf, "COM port: COM%d", com_port + 1);
    send_line(buf);
    send_crlf();

    /* Command line */
    send_line("Command line arguments:");
    for (i = 0; i < argc; i++) {
        sprintf(buf, "  argv[%d] = %s", i, argv[i]);
        send_line(buf);
    }
    send_crlf();

    /* Show dropfiles - raw then parsed */
    show_file("C:\\DOOR.SYS", "C:\\DOOR.SYS (raw)");
    show_dropfile_parsed("C:\\DOOR.SYS", "DOOR.SYS", doorsys_fields);

    show_file("C:\\DORINFO1.DEF", "C:\\DORINFO1.DEF (raw)");
    show_dropfile_parsed("C:\\DORINFO1.DEF", "DORINFO1.DEF", dorinfo_fields);

    show_file("C:\\CHAIN.TXT", "C:\\CHAIN.TXT (raw)");
    show_dropfile_parsed("C:\\CHAIN.TXT", "CHAIN.TXT", chaintxt_fields);

    show_file("C:\\CALLINFO.BBS", "C:\\CALLINFO.BBS (raw)");
    show_dropfile_parsed("C:\\CALLINFO.BBS", "CALLINFO.BBS", callinfo_fields);

    show_file("C:\\SFDOORS.DAT", "C:\\SFDOORS.DAT (raw)");
    show_dropfile_parsed("C:\\SFDOORS.DAT", "SFDOORS.DAT", sfdoors_fields);
    send_crlf();

    /* Interactive echo test */
    send_line("============================================");
    send_line("  Interactive echo test");
    send_line("  Type text + Enter. Q to quit.");
    send_line("============================================");

    while (1) {
        int pos = 0;
        send_str("> ");

        while (1) {
            c = serial_recv_wait();
            if (c == '\r' || c == '\n') {
                buf[pos] = '\0';
                send_crlf();
                break;
            }
            if (c == 8 || c == 127) {  /* backspace */
                if (pos > 0) {
                    pos--;
                    send_str("\x08 \x08");
                }
                continue;
            }
            if (pos < MAX_LINE - 1 && c >= 32) {
                buf[pos++] = c;
                serial_send_char(c);
            }
        }

        if (buf[0] == 'q' || buf[0] == 'Q') {
            if (pos <= 1) break;
        }

        send_str("Echo: ");
        send_line(buf);
    }

    send_crlf();
    send_line("Goodbye from Test Door!");

    /* Cleanup */
    if (fossil_active) {
        fossil_deinit(com_port);
    }

    return 0;
}
