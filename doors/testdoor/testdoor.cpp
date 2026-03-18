/* ============================================================
 * TESTDOOR.CPP  -  BBS Diagnostic Test Door
 * Turbo C++ 3.x / Borland C++ (DOS target)
 *
 * Compile:  tcc testdoor.cpp
 *   -or-    bcc testdoor.cpp
 *
 * Command line:
 *   TESTDOOR [COM<n>[:<baud>] | FOSSIL<n> | LOCAL] [droppath]
 *
 *   COM<n>       Direct UART on COM port n (1-4)
 *                Append :<baud> to set baud rate, e.g. COM1:38400
 *   FOSSIL<n>    Use FOSSIL driver on COM port n (1-4)
 *   LOCAL        Console-only mode (no COM port; useful for testing)
 *   droppath     Directory containing dropfiles (default: .\)
 *
 * Examples:
 *   TESTDOOR FOSSIL1 C:\BBS\NODE1\
 *   TESTDOOR COM1:57600 C:\RENEGADE\NODE\
 *   TESTDOOR COM2
 *   TESTDOOR LOCAL C:\BBS\
 *
 * Dropfiles detected (searched in current priority order):
 *   DOOR.SYS      - GAP / generic (most universal)
 *   DORINFO1.DEF  - RBBS / QuickBBS / Remote Access
 *   CALLINFO.BBS  - Wildcat! BBS
 *   CHAIN.TXT     - WWIV BBS
 * ============================================================ */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdarg.h>
#include <dos.h>
#include <conio.h>

/* ============================================================
 * Constants
 * ============================================================ */

#define MODE_FOSSIL  0
#define MODE_COM     1
#define MODE_LOCAL   2

/* UART register offsets from port base address */
#define UART_RBR    0       /* Receive Buffer Register  (read)  */
#define UART_THR    0       /* Transmit Holding Register(write) */
#define UART_IER    1       /* Interrupt Enable Register        */
#define UART_FCR    2       /* FIFO Control Register (16550+)   */
#define UART_LCR    3       /* Line Control Register            */
#define UART_MCR    4       /* Modem Control Register           */
#define UART_LSR    5       /* Line Status Register             */

#define LSR_DR      0x01    /* Bit 0: RX Data Ready             */
#define LSR_THRE    0x20    /* Bit 5: TX Holding Register Empty */

static const unsigned int COM_BASE[5] = { 0, 0x3F8, 0x2F8, 0x3E8, 0x2E8 };

/* ============================================================
 * Global state
 * ============================================================ */

static int          g_mode = MODE_FOSSIL;
static int          g_port = 1;             /* 1-based COM port # */
static unsigned int g_baud = 38400U;
static char         g_path[132] = ".\\";

/* ============================================================
 * FOSSIL Driver  (INT 14h extensions, X00/BNU/ZedZap/etc.)
 * ============================================================ */

/*
 * fossil_init - Activate FOSSIL on port, verify driver presence.
 * Returns 1 if FOSSIL driver responded with 0x1954 signature.
 */
int fossil_init(int port)
{
    union REGS r;
    r.h.ah = 0x04;                  /* FOSSIL init function         */
    r.x.bx = 0x4F49;               /* 'IO' - required signature    */
    r.x.dx = (unsigned)(port - 1); /* 0-based port index           */
    int86(0x14, &r, &r);
    return (r.x.ax == 0x1954) ? 1 : 0;
}

void fossil_deinit(int port)
{
    union REGS r;
    r.h.ah = 0x05;
    r.x.dx = (unsigned)(port - 1);
    int86(0x14, &r, &r);
}

/* Send one character; blocks until driver accepts it */
void fossil_putch(int port, unsigned char c)
{
    union REGS r;
    r.h.ah = 0x01;
    r.h.dl = c;
    r.x.dx = (unsigned)(port - 1);
    int86(0x14, &r, &r);
}

/*
 * fossil_status - INT 14h AH=03h.
 * Returns AX: AH = line status (LSR), AL = modem status (MSR).
 * AH bit 0 = RX char ready; AH bit 5 = TX empty.
 */
static unsigned int fossil_status(int port)
{
    union REGS r;
    r.h.ah = 0x03;
    r.x.dx = (unsigned)(port - 1);
    int86(0x14, &r, &r);
    return r.x.ax;
}

int fossil_kbhit(int port)
{
    return (fossil_status(port) & 0x0100) ? 1 : 0; /* AH bit 0 */
}

/* Blocking receive - FOSSIL spec guarantees AL = char on return */
int fossil_getch(int port)
{
    union REGS r;
    r.h.ah = 0x02;
    r.x.dx = (unsigned)(port - 1);
    int86(0x14, &r, &r);
    return (int)(unsigned char)r.h.al;
}

/* ============================================================
 * Direct UART Access
 * ============================================================ */

/*
 * com_init - Program the UART: 8N1 at <baud>, polled mode (no IRQ).
 * The BBS will already have the modem connected; we just set rate/format.
 */
int com_init(int port, unsigned int baud)
{
    unsigned int base, div;
    if (port < 1 || port > 4) return 0;
    base = COM_BASE[port];

    /* Baud rate divisor: UART crystal is 1.8432 MHz, clock div = 16,
       so divisor = 1843200 / 16 / baud = 115200 / baud               */
    div = (unsigned int)(115200UL / (unsigned long)baud);
    if (!div) div = 1;

    outportb(base + UART_IER, 0x00);         /* disable all UART IRQs   */
    outportb(base + UART_LCR, 0x80);         /* DLAB = 1                */
    outportb(base + UART_RBR, div & 0xFF);   /* divisor latch LSB       */
    outportb(base + UART_IER, div >> 8);     /* divisor latch MSB       */
    outportb(base + UART_LCR, 0x03);         /* 8N1; clears DLAB        */
    outportb(base + UART_FCR, 0xC7);         /* enable+clear FIFOs      */
    outportb(base + UART_MCR, 0x0B);         /* DTR | RTS | OUT2        */
    return 1;
}

void com_putch(int port, unsigned char c)
{
    unsigned int base = COM_BASE[port];
    while (!(inportb(base + UART_LSR) & LSR_THRE))
        ;                               /* spin until TX buffer empty  */
    outportb(base + UART_THR, c);
}

int com_kbhit(int port)
{
    return (inportb(COM_BASE[port] + UART_LSR) & LSR_DR) ? 1 : 0;
}

int com_getch(int port)
{
    unsigned int base = COM_BASE[port];
    while (!(inportb(base + UART_LSR) & LSR_DR))
        ;                               /* spin until byte arrives     */
    return (int)inportb(base + UART_RBR);
}

/* ============================================================
 * Unified Door I/O  (wraps COM / FOSSIL / LOCAL transparently)
 * ============================================================ */

void door_putch(unsigned char c)
{
    switch (g_mode) {
        case MODE_FOSSIL: fossil_putch(g_port, c); return;
        case MODE_COM:    com_putch(g_port, c);    return;
        case MODE_LOCAL:  putchar(c);              return;
    }
}

/* Outputs string, converting bare \n to \r\n for teletype convention */
void door_puts(const char *s)
{
    for (; *s; ++s) {
        if (*s == '\n') door_putch('\r');
        door_putch((unsigned char)*s);
    }
}

void door_printf(const char *fmt, ...)
{
    char buf[512];
    va_list ap;
    va_start(ap, fmt);
    vsprintf(buf, fmt, ap);
    va_end(ap);
    door_puts(buf);
}

int door_kbhit(void)
{
    switch (g_mode) {
        case MODE_FOSSIL: return fossil_kbhit(g_port);
        case MODE_COM:    return com_kbhit(g_port);
        case MODE_LOCAL:  return kbhit();
    }
    return 0;
}

int door_getch(void)
{
    switch (g_mode) {
        case MODE_FOSSIL: return fossil_getch(g_port);
        case MODE_COM:    return com_getch(g_port);
        case MODE_LOCAL:  return getch();
    }
    return 0;
}

/* Divider line helper */
void door_line(char ch, int n)
{
    int i;
    for (i = 0; i < n; i++) door_putch((unsigned char)ch);
    door_puts("\n");
}

/* ============================================================
 * Dropfile Data Structure
 * ============================================================ */

#define MAX_RAW  56  /* max stored raw lines per dropfile */

typedef struct {
    int  detected;
    char filename[20];

    /* Parsed fields (populated as available per format) */
    char bbs_name    [64];
    char sysop       [64];
    char com_port    [16];
    long baud_rate;
    char user_name   [64];  /* handle / login name          */
    char user_real   [64];  /* real / legal name            */
    char location    [64];  /* city, state                  */
    char home_phone  [32];
    char data_phone  [32];
    char password    [32];  /* often blank or scrambled     */
    int  security_level;
    long total_calls;
    char last_date   [24];
    int  time_left_secs;
    int  time_left_mins;
    char graphics    [8];   /* GR / NG / 7E / RIP           */
    int  page_length;
    int  expert_mode;
    int  node_num;
    char user_number [16];

    /* Every line stored verbatim for full display */
    char raw_label[MAX_RAW][24];
    char raw_value[MAX_RAW][80];
    int  raw_count;
} DropInfo;

/* Store a labelled raw line */
static void raw_store(DropInfo *d, int lnum, const char *label, const char *val)
{
    int i = d->raw_count;
    if (i >= MAX_RAW) return;
    sprintf(d->raw_label[i], "L%-2d %-18s", lnum, label);
    strncpy(d->raw_value[i], val, 79);
    d->raw_value[i][79] = '\0';
    d->raw_count++;
}

/* Read next line from f, strip CR/LF. Returns 1 ok, 0 EOF. */
static int fget_line(FILE *f, char *buf, int size)
{
    int len;
    if (!fgets(buf, size, f)) return 0;
    len = strlen(buf);
    while (len > 0 && (buf[len-1]=='\r' || buf[len-1]=='\n'))
        buf[--len] = '\0';
    return 1;
}

/* ============================================================
 * DOOR.SYS Parser  (GAP format, the most widely supported)
 *
 * Line #  Field
 *  0      COM port name (e.g. "COM1:")
 *  1      Baud rate
 *  2      Parity / data bits (usually "8")
 *  3      Node number
 *  4      DTE locked baud rate
 *  5      Screen display flag (Y/N)
 *  6      Printer flag (Y/N)
 *  7      Page bell (Y/N)
 *  8      Caller alarm (Y/N)
 *  9      User's real / full name
 * 10      City, State
 * 11      Home phone
 * 12      Data / work phone
 * 13      Password (often scrambled)
 * 14      Security level
 * 15      Total times called
 * 16      Last call date (MM/DD/YY)
 * 17      Seconds remaining this call
 * 18      Minutes remaining this call
 * 19      Graphics mode (GR / NG / 7E / RIP)
 * 20      Page length (screen rows)
 * 21      Expert mode (Y/N)
 * 22      Current conference number
 * 23      Current conference name  (some BBSes: expiry date)
 * 24      User record number
 * 25      Account balance / credits
 * 26      User's handle / alias
 * ============================================================ */
void parse_door_sys(DropInfo *d)
{
    char fname[132], line[256];
    FILE *f;
    int   n;
    static const char *labels[] = {
        "COM port", "Baud rate", "Parity/bits", "Node number",
        "DTE baud", "Screen Y/N", "Printer Y/N", "Page bell Y/N",
        "Caller alarm Y/N", "Real name", "City/State", "Home phone",
        "Data phone", "Password", "Security level", "Total calls",
        "Last call date", "Seconds remain", "Minutes remain",
        "Graphics", "Page length", "Expert mode Y/N", "Conf number",
        "Conf name", "User number", "Acct balance", "Handle/alias"
    };

    sprintf(fname, "%sDOOR.SYS", g_path);
    f = fopen(fname, "r");
    if (!f) return;

    d->detected = 1;
    strcpy(d->filename, "DOOR.SYS");
    d->raw_count = 0;

    for (n = 0; n < 52 && fget_line(f, line, sizeof(line)); n++) {
        const char *lbl = (n < 27) ? labels[n] : "(extra)";
        raw_store(d, n, lbl, line);
        switch (n) {
        case  0: strncpy(d->com_port,        line, 15); break;
        case  1: d->baud_rate      = atol(line);        break;
        case  3: d->node_num       = atoi(line);        break;
        case  9: strncpy(d->user_real,        line, 63); break;
        case 10: strncpy(d->location,         line, 63); break;
        case 11: strncpy(d->home_phone,       line, 31); break;
        case 12: strncpy(d->data_phone,       line, 31); break;
        case 13: strncpy(d->password,         line, 31); break;
        case 14: d->security_level = atoi(line);        break;
        case 15: d->total_calls    = atol(line);        break;
        case 16: strncpy(d->last_date,        line, 23); break;
        case 17: d->time_left_secs = atoi(line);        break;
        case 18: d->time_left_mins = atoi(line);        break;
        case 19: strncpy(d->graphics,         line,  7); break;
        case 20: d->page_length    = atoi(line);        break;
        case 21: d->expert_mode    = (toupper(line[0])=='Y') ? 1 : 0; break;
        case 24: strncpy(d->user_number,      line, 15); break;
        case 26: strncpy(d->user_name,        line, 63); break;
        }
    }
    fclose(f);

    if (!d->user_name[0])
        strncpy(d->user_name, d->user_real, 63);
}

/* ============================================================
 * DORINFO1.DEF Parser  (RBBS-PC / QuickBBS / Remote Access)
 *
 * Line #  Field
 *  0      BBS name
 *  1      Sysop first name
 *  2      Sysop last name
 *  3      COM port ("COM1" ... "COM4", or "NONE" for local)
 *  4      Baud rate (0 = local)
 *  5      (reserved, usually "0")
 *  6      User first name
 *  7      User last name
 *  8      User city, state
 *  9      ANSI graphics (1=yes, 0=no, -1=7-bit ANSI)
 * 10      Security level
 * 11      Time remaining in minutes
 * 12      FOSSIL flag (-1 typical)
 * ============================================================ */
void parse_dorinfo(DropInfo *d)
{
    char fname[132], line[256];
    char sfirst[32], slast[32], ufirst[32], ulast[32];
    FILE *f;
    int   n;
    static const char *labels[] = {
        "BBS name", "Sysop first", "Sysop last", "COM port",
        "Baud rate", "(reserved)", "User first", "User last",
        "City/State", "ANSI flag", "Security level",
        "Time left (min)", "FOSSIL flag"
    };

    sprintf(fname, "%sDORINFO1.DEF", g_path);
    f = fopen(fname, "r");
    if (!f) {
        sprintf(fname, "%sDORINFO.DEF", g_path);
        f = fopen(fname, "r");
        if (!f) return;
        strcpy(d->filename, "DORINFO.DEF");
    } else {
        strcpy(d->filename, "DORINFO1.DEF");
    }

    d->detected = 1;
    d->raw_count = 0;
    sfirst[0] = slast[0] = ufirst[0] = ulast[0] = '\0';

    for (n = 0; n < 13 && fget_line(f, line, sizeof(line)); n++) {
        const char *lbl = (n < 13) ? labels[n] : "(extra)";
        raw_store(d, n, lbl, line);
        switch (n) {
        case  0: strncpy(d->bbs_name,       line, 63); break;
        case  1: strncpy(sfirst,             line, 31); break;
        case  2: strncpy(slast,              line, 31); break;
        case  3: strncpy(d->com_port,        line, 15); break;
        case  4: d->baud_rate = atol(line);             break;
        case  6: strncpy(ufirst,             line, 31); break;
        case  7: strncpy(ulast,              line, 31); break;
        case  8: strncpy(d->location,        line, 63); break;
        case  9:
            if (line[0]=='-')      strcpy(d->graphics, "7E");
            else if (line[0]=='1') strcpy(d->graphics, "GR");
            else                   strcpy(d->graphics, "NG");
            break;
        case 10: d->security_level = atoi(line); break;
        case 11: d->time_left_mins  = atoi(line); break;
        }
    }
    fclose(f);

    sprintf(d->sysop,     "%.31s %.31s", sfirst, slast);
    sprintf(d->user_name, "%.31s %.31s", ufirst, ulast);
    strncpy(d->user_real, d->user_name, 63);
}

/* ============================================================
 * CALLINFO.BBS Parser  (Wildcat! BBS)
 *
 * Line #  Field
 *  0      User name (handle)
 *  1      Baud rate (0 = local)
 *  2      ANSI graphics (1=yes, 0=no)
 *  3      Security level
 *  4      Time remaining (minutes)
 *  5      Sysop available flag (Y/N)
 *  6      User's real name
 *  7      City, State
 *  8      Home phone
 *  9      Data phone
 * 10      Total calls to system
 * 11      Last call date
 * 12      Screen page length
 * 13      Expert mode (Y/N)
 * 14      User record number
 * ============================================================ */
void parse_callinfo(DropInfo *d)
{
    char fname[132], line[256];
    FILE *f;
    int   n;
    static const char *labels[] = {
        "User name", "Baud rate", "ANSI (1=yes)", "Security level",
        "Time left (min)", "Sysop avail Y/N", "Real name", "City/State",
        "Home phone", "Data phone", "Total calls", "Last call date",
        "Page length", "Expert mode Y/N", "User record #"
    };

    sprintf(fname, "%sCALLINFO.BBS", g_path);
    f = fopen(fname, "r");
    if (!f) return;

    d->detected = 1;
    strcpy(d->filename, "CALLINFO.BBS");
    d->raw_count = 0;

    for (n = 0; n < 40 && fget_line(f, line, sizeof(line)); n++) {
        const char *lbl = (n < 15) ? labels[n] : "(extra)";
        raw_store(d, n, lbl, line);
        switch (n) {
        case  0: strncpy(d->user_name,    line, 63); break;
        case  1: d->baud_rate  = atol(line);         break;
        case  2:
            if (line[0]=='1') strcpy(d->graphics,"GR");
            else              strcpy(d->graphics,"NG");
            break;
        case  3: d->security_level = atoi(line);     break;
        case  4: d->time_left_mins  = atoi(line);    break;
        case  6: strncpy(d->user_real,    line, 63); break;
        case  7: strncpy(d->location,     line, 63); break;
        case  8: strncpy(d->home_phone,   line, 31); break;
        case  9: strncpy(d->data_phone,   line, 31); break;
        case 10: d->total_calls   = atol(line);      break;
        case 11: strncpy(d->last_date,    line, 23); break;
        case 12: d->page_length   = atoi(line);      break;
        case 13: d->expert_mode   = (toupper(line[0])=='Y') ? 1 : 0; break;
        case 14: strncpy(d->user_number,  line, 15); break;
        }
    }
    fclose(f);
}

/* ============================================================
 * CHAIN.TXT Parser  (WWIV BBS)
 *
 * Line #  Field
 *  0      User record number
 *  1      User name (handle)
 *  2      User real name
 *  3      Callsign (ham radio, or blank)
 *  4      Security level (SL)
 *  5      Time remaining (minutes)
 *  6      Co-sysop flag (1=yes)
 *  7      System number (node)
 *  8      User number
 *  9      Page length
 * 10      ANSI (1=yes)
 * 11      Location (city, state)
 * 12      Home phone
 * 13      Data phone
 * ============================================================ */
void parse_chain_txt(DropInfo *d)
{
    char fname[132], line[256];
    FILE *f;
    int   n;
    static const char *labels[] = {
        "User record #", "User name", "Real name", "Callsign",
        "Security level", "Time left (min)", "CoSysop flag",
        "System/node #", "User number", "Page length",
        "ANSI (1=yes)", "City/State", "Home phone", "Data phone"
    };

    sprintf(fname, "%sCHAIN.TXT", g_path);
    f = fopen(fname, "r");
    if (!f) return;

    d->detected = 1;
    strcpy(d->filename, "CHAIN.TXT");
    d->raw_count = 0;

    for (n = 0; n < 40 && fget_line(f, line, sizeof(line)); n++) {
        const char *lbl = (n < 14) ? labels[n] : "(extra)";
        raw_store(d, n, lbl, line);
        switch (n) {
        case  0: strncpy(d->user_number,  line, 15); break;
        case  1: strncpy(d->user_name,    line, 63); break;
        case  2: strncpy(d->user_real,    line, 63); break;
        case  4: d->security_level = atoi(line);     break;
        case  5: d->time_left_mins  = atoi(line);    break;
        case  7: d->node_num        = atoi(line);    break;
        case  9: d->page_length     = atoi(line);    break;
        case 10:
            if (line[0]=='1') strcpy(d->graphics,"GR");
            else              strcpy(d->graphics,"NG");
            break;
        case 11: strncpy(d->location,     line, 63); break;
        case 12: strncpy(d->home_phone,   line, 31); break;
        case 13: strncpy(d->data_phone,   line, 31); break;
        }
    }
    fclose(f);
}

/* ============================================================
 * Display helpers
 * ============================================================ */

static void show_field(const char *label, const char *val)
{
    if (val && val[0])
        door_printf("  %-22s: %s\n", label, val);
    else
        door_printf("  %-22s: (not set)\n", label);
}

static void show_int(const char *label, int val)
{
    char buf[32];
    sprintf(buf, "%d", val);
    show_field(label, buf);
}

static void show_long(const char *label, long val)
{
    char buf[32];
    sprintf(buf, "%ld", val);
    show_field(label, buf);
}

static void show_dropinfo(DropInfo *d)
{
    int i;

    door_printf("\n  File     : %s\n", d->filename);
    door_line('-', 60);

    /* Show all raw lines exactly as they appeared in the file */
    for (i = 0; i < d->raw_count; i++)
        door_printf("  %-24s: %s\n", d->raw_label[i], d->raw_value[i]);

    /* Summary of interpreted values */
    door_line('-', 60);
    door_puts("  >> Interpreted fields:\n");
    if (d->bbs_name[0])       show_field("BBS Name",       d->bbs_name);
    if (d->sysop[0])          show_field("Sysop",          d->sysop);
    show_field("User Handle",          d->user_name);
    show_field("User Real Name",       d->user_real);
    show_field("Location",             d->location);
    show_field("COM Port",             d->com_port);
    if (d->baud_rate)         show_long ("Baud Rate",       d->baud_rate);
    show_int ("Node #",                d->node_num);
    show_field("User Record #",        d->user_number);
    show_int ("Security Level",        d->security_level);
    show_long("Total Calls",           d->total_calls);
    show_field("Last Call Date",       d->last_date);
    show_int ("Time Left (mins)",      d->time_left_mins);
    show_int ("Time Left (secs)",      d->time_left_secs);
    show_field("Graphics Mode",        d->graphics);
    show_int ("Page Length",           d->page_length);
    show_int ("Expert Mode",           d->expert_mode);
    show_field("Home Phone",           d->home_phone);
    show_field("Data Phone",           d->data_phone);
    if (d->password[0])       show_field("Password",       d->password);
}

/* ============================================================
 * Command Line Parser
 * ============================================================ */

static void strupr_local(char *s)
{
    for (; *s; s++) *s = (char)toupper((unsigned char)*s);
}

/*
 * Parses:
 *   FOSSIL<n>        -> g_mode=FOSSIL, g_port=n
 *   COM<n>           -> g_mode=COM,    g_port=n, g_baud=38400
 *   COM<n>:<baud>    -> g_mode=COM,    g_port=n, g_baud=baud
 *   LOCAL            -> g_mode=LOCAL
 *   <path>           -> g_path (anything containing \ or / or ending in \)
 */
static void parse_args(int argc, char *argv[])
{
    int i;
    char tok[132];

    for (i = 1; i < argc; i++) {
        strncpy(tok, argv[i], 131);
        tok[131] = '\0';
        strupr_local(tok);

        if (strncmp(tok, "FOSSIL", 6) == 0) {
            g_mode = MODE_FOSSIL;
            g_port = atoi(tok + 6);
            if (g_port < 1 || g_port > 4) g_port = 1;
        }
        else if (strncmp(tok, "COM", 3) == 0 && isdigit((unsigned char)tok[3])) {
            char *colon;
            g_mode = MODE_COM;
            g_port = tok[3] - '0';
            if (g_port < 1 || g_port > 4) g_port = 1;
            colon = strchr(tok + 3, ':');
            if (colon) {
                g_baud = (unsigned int)atol(colon + 1);
                if (!g_baud) g_baud = 38400U;
            }
        }
        else if (strcmp(tok, "LOCAL") == 0) {
            g_mode = MODE_LOCAL;
        }
        else {
            /* Treat as dropfile path */
            strncpy(g_path, argv[i], 131);
            /* Ensure trailing backslash */
            {
                int len = strlen(g_path);
                if (len > 0 && g_path[len-1] != '\\' && g_path[len-1] != '/')
                {
                    g_path[len]   = '\\';
                    g_path[len+1] = '\0';
                }
            }
        }
    }
}

/* Reconstruct full command line from argv for display */
static void build_cmdline(int argc, char *argv[], char *out, int outsize)
{
    int i, pos = 0;
    for (i = 0; i < argc && pos < outsize - 2; i++) {
        int len = strlen(argv[i]);
        if (pos + len + 1 >= outsize) break;
        if (i > 0) out[pos++] = ' ';
        strcpy(out + pos, argv[i]);
        pos += len;
    }
    out[pos] = '\0';
}

/* ============================================================
 * main
 * ============================================================ */
int main(int argc, char *argv[])
{
    char     cmdline[256];
    DropInfo drops[4];
    int      i, any;
    static const char *mode_names[] = { "FOSSIL", "COM (direct UART)", "LOCAL (console)" };

    /* Default dropfile path */
    strcpy(g_path, ".\\");

    /* Parse command line */
    parse_args(argc, argv);

    /* Save original command line for display */
    build_cmdline(argc, argv, cmdline, sizeof(cmdline));

    /* Initialize COM/FOSSIL */
    if (g_mode == MODE_FOSSIL) {
        if (!fossil_init(g_port)) {
            /* FOSSIL not found - fall back to local so we can at least report */
            fprintf(stderr, "FOSSIL driver not found on COM%d - falling back to LOCAL.\r\n", g_port);
            g_mode = MODE_LOCAL;
        }
    }
    else if (g_mode == MODE_COM) {
        if (!com_init(g_port, g_baud)) {
            fprintf(stderr, "Invalid COM port %d.\r\n", g_port);
            return 1;
        }
    }

    /* Search all four dropfile types */
    memset(drops, 0, sizeof(drops));
    parse_door_sys (&drops[0]);
    parse_dorinfo  (&drops[1]);
    parse_callinfo (&drops[2]);
    parse_chain_txt(&drops[3]);

    /* ---- Display ---- */
    door_line('=', 60);
    door_puts("           BBS DIAGNOSTIC TEST DOOR\n");
    door_puts("         COM / FOSSIL Support Checker\n");
    door_line('=', 60);

    door_puts("\n>> Connection Info\n");
    door_line('-', 60);
    door_printf("  Mode             : %s\n", mode_names[g_mode]);
    if (g_mode == MODE_FOSSIL)
        door_printf("  FOSSIL port      : COM%d\n", g_port);
    else if (g_mode == MODE_COM)
        door_printf("  COM port / baud  : COM%d at %u bps\n", g_port, g_baud);

    door_puts("\n>> Command Line Received\n");
    door_line('-', 60);
    door_printf("  argc = %d\n", argc);
    door_printf("  argv = %s\n", cmdline[0] ? cmdline : "(none)");
    if (argc > 1) {
        for (i = 0; i < argc; i++)
            door_printf("    argv[%d] = %s\n", i, argv[i]);
    }

    door_printf("\n>> Dropfile Search Path: %s\n", g_path);
    door_line('-', 60);

    /* Which dropfiles were found? */
    any = 0;
    for (i = 0; i < 4; i++)
        if (drops[i].detected) { any++; }

    if (!any) {
        door_puts("  No dropfiles detected in search path.\n");
    } else {
        door_printf("  Found %d dropfile(s):\n", any);
        for (i = 0; i < 4; i++)
            if (drops[i].detected)
                door_printf("    [+] %s\n", drops[i].filename);
            else {
                /* Show which ones were NOT found */
                static const char *names[] = {
                    "DOOR.SYS", "DORINFO1.DEF", "CALLINFO.BBS", "CHAIN.TXT"
                };
                door_printf("    [ ] %s  (not present)\n", names[i]);
            }
    }

    /* Dump each detected dropfile */
    for (i = 0; i < 4; i++) {
        if (!drops[i].detected) continue;
        door_printf("\n>> Dropfile: %s\n", drops[i].filename);
        show_dropinfo(&drops[i]);
    }

    /* Footer */
    door_puts("\n");
    door_line('=', 60);
    door_puts("  Diagnostic complete.  Press any key to exit...\n");
    door_line('=', 60);

    /* Wait for keypress */
    while (!door_kbhit())
        ;
    door_getch();

    /* Clean up */
    if (g_mode == MODE_FOSSIL)
        fossil_deinit(g_port);

    return 0;
}
