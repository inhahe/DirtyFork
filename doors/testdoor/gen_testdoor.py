"""
Generate TESTDOOR.COM - a DOS test door that tests serial communication.
Supports FOSSIL (INT 14h extended) and BIOS serial (INT 14h basic).
Also reads and displays DOOR.SYS from C:\.

Run this script to generate TESTDOOR.COM, then use it in DOSBox.
"""

import struct

class Asm:
    """Minimal x86 assembler for .COM files (org 100h)."""
    def __init__(self):
        self.code = bytearray()
        self.labels = {}
        self.fixups = []  # (offset, label, type) where type is 'rel8' or 'rel16'

    def pos(self):
        return len(self.code)

    def label(self, name):
        self.labels[name] = self.pos()

    def db(self, *args):
        for a in args:
            if isinstance(a, bytes):
                self.code.extend(a)
            elif isinstance(a, str):
                self.code.extend(a.encode('cp437'))
            elif isinstance(a, int):
                self.code.extend(bytes([a & 0xFF]))

    def dw(self, val):
        self.code.extend(struct.pack('<H', val & 0xFFFF))

    def raw(self, *bs):
        """Emit raw bytes."""
        for b in bs:
            self.code.append(b & 0xFF)

    def jmp_short(self, label):
        self.raw(0xEB)
        self.fixups.append((self.pos(), label, 'rel8'))
        self.raw(0x00)

    def je_short(self, label):
        self.raw(0x74)
        self.fixups.append((self.pos(), label, 'rel8'))
        self.raw(0x00)

    def jne_short(self, label):
        self.raw(0x75)
        self.fixups.append((self.pos(), label, 'rel8'))
        self.raw(0x00)

    def jnz_short(self, label):
        return self.jne_short(label)

    def jz_short(self, label):
        return self.je_short(label)

    def jc_short(self, label):
        self.raw(0x72)
        self.fixups.append((self.pos(), label, 'rel8'))
        self.raw(0x00)

    def call_near(self, label):
        self.raw(0xE8)
        self.fixups.append((self.pos(), label, 'rel16'))
        self.dw(0x0000)

    def jmp_near(self, label):
        self.raw(0xE9)
        self.fixups.append((self.pos(), label, 'rel16'))
        self.dw(0x0000)

    def resolve(self):
        for offset, label, ftype in self.fixups:
            target = self.labels[label]
            if ftype == 'rel8':
                rel = target - (offset + 1)
                if rel < -128 or rel > 127:
                    raise ValueError(f"rel8 overflow for {label}: {rel}")
                self.code[offset] = rel & 0xFF
            elif ftype == 'rel16':
                rel = target - (offset + 2)
                struct.pack_into('<h', self.code, offset, rel)

    def build(self):
        self.resolve()
        return bytes(self.code)


def generate():
    a = Asm()

    # ===== Entry point =====
    # Try FOSSIL init: INT 14h AH=04h DX=0 (COM1)
    a.raw(0xB4, 0x04)          # mov ah, 04h
    a.raw(0xBA, 0x00, 0x00)    # mov dx, 0 (COM1)
    a.raw(0xCD, 0x14)          # int 14h
    a.raw(0x3D, 0x54, 0x19)    # cmp ax, 1954h
    a.je_short('fossil_ok')

    # No FOSSIL - init BIOS serial: AH=00h AL=E3h (9600,N,8,1)
    a.raw(0xB4, 0x00)          # mov ah, 00h
    a.raw(0xB0, 0xE3)          # mov al, E3h
    a.raw(0xBA, 0x00, 0x00)    # mov dx, 0
    a.raw(0xCD, 0x14)          # int 14h

    # Send "BIOS serial mode" message
    a.raw(0xBE)                # mov si, msg_bios
    a.fixups.append((a.pos(), 'msg_bios', 'rel16_abs'))
    a.dw(0)
    a.call_near('send_str')
    a.jmp_short('after_init')

    a.label('fossil_ok')
    # Send "FOSSIL detected" message
    a.raw(0xBE)                # mov si, msg_fossil
    a.fixups.append((a.pos(), 'msg_fossil', 'rel16_abs'))
    a.dw(0)
    a.call_near('send_str')

    a.label('after_init')

    # Send header
    a.raw(0xBE)
    a.fixups.append((a.pos(), 'msg_header', 'rel16_abs'))
    a.dw(0)
    a.call_near('send_str')

    # Send command line from PSP (at 80h = length, 81h..FFh = text)
    a.raw(0xBE)
    a.fixups.append((a.pos(), 'msg_cmdline', 'rel16_abs'))
    a.dw(0)
    a.call_near('send_str')

    # Send actual command line from PSP
    a.raw(0x31, 0xC9)          # xor cx, cx
    a.raw(0x8A, 0x0E, 0x80, 0x00)  # mov cl, [0080h]
    a.raw(0xBE, 0x81, 0x00)    # mov si, 0081h
    a.call_near('send_n')

    # Send CRLF
    a.raw(0xBE)
    a.fixups.append((a.pos(), 'msg_crlf', 'rel16_abs'))
    a.dw(0)
    a.call_near('send_str')
    a.raw(0xBE)
    a.fixups.append((a.pos(), 'msg_crlf', 'rel16_abs'))
    a.dw(0)
    a.call_near('send_str')

    # Try to open and display C:\DOOR.SYS
    a.raw(0xBE)
    a.fixups.append((a.pos(), 'msg_doorsys', 'rel16_abs'))
    a.dw(0)
    a.call_near('send_str')
    a.raw(0xBA)                # mov dx, filename_doorsys
    a.fixups.append((a.pos(), 'fn_doorsys', 'rel16_abs'))
    a.dw(0)
    a.call_near('show_file')

    # Try to open and display C:\DOOR32.SYS
    a.raw(0xBE)
    a.fixups.append((a.pos(), 'msg_door32', 'rel16_abs'))
    a.dw(0)
    a.call_near('send_str')
    a.raw(0xBA)                # mov dx, filename_door32
    a.fixups.append((a.pos(), 'fn_door32', 'rel16_abs'))
    a.dw(0)
    a.call_near('show_file')

    # Send echo prompt
    a.raw(0xBE)
    a.fixups.append((a.pos(), 'msg_echo', 'rel16_abs'))
    a.dw(0)
    a.call_near('send_str')

    # ===== Echo loop =====
    a.label('echo_loop')
    # Send prompt "> "
    a.raw(0xB0, 0x3E)         # mov al, '>'
    a.call_near('send_char')
    a.raw(0xB0, 0x20)         # mov al, ' '
    a.call_near('send_char')

    a.label('echo_read')
    # Read char from serial
    a.raw(0xB4, 0x02)         # mov ah, 02h (FOSSIL/BIOS read)
    a.raw(0xBA, 0x00, 0x00)   # mov dx, 0
    a.raw(0xCD, 0x14)         # int 14h
    a.raw(0x80, 0xFC, 0x00)   # cmp ah, 0
    a.jnz_short('echo_read')  # no char ready, retry

    # Check for 'q' or 'Q'
    a.raw(0x3C, 0x71)         # cmp al, 'q'
    a.je_short('done')
    a.raw(0x3C, 0x51)         # cmp al, 'Q'
    a.je_short('done')

    # Check for CR
    a.raw(0x3C, 0x0D)         # cmp al, CR
    a.je_short('echo_cr')

    # Echo the char back
    a.call_near('send_char')
    a.jmp_short('echo_read')

    a.label('echo_cr')
    a.raw(0xB0, 0x0D)         # mov al, CR
    a.call_near('send_char')
    a.raw(0xB0, 0x0A)         # mov al, LF
    a.call_near('send_char')
    a.jmp_short('echo_loop')

    # ===== Exit =====
    a.label('done')
    a.raw(0xBE)
    a.fixups.append((a.pos(), 'msg_bye', 'rel16_abs'))
    a.dw(0)
    a.call_near('send_str')

    # Deinit FOSSIL
    a.raw(0xB4, 0x05)         # mov ah, 05h
    a.raw(0xBA, 0x00, 0x00)   # mov dx, 0
    a.raw(0xCD, 0x14)         # int 14h

    # Exit to DOS
    a.raw(0xB4, 0x4C)         # mov ah, 4Ch
    a.raw(0xB0, 0x00)         # mov al, 0
    a.raw(0xCD, 0x21)         # int 21h

    # ===== Subroutines =====

    # send_char: send AL over COM1 via INT 14h AH=01h
    a.label('send_char')
    a.raw(0x50)                # push ax
    a.raw(0xB4, 0x01)         # mov ah, 01h
    a.raw(0xBA, 0x00, 0x00)   # mov dx, 0
    a.raw(0xCD, 0x14)         # int 14h
    a.raw(0x58)                # pop ax
    a.raw(0xC3)                # ret

    # send_str: send null-terminated string at DS:SI via send_char
    a.label('send_str')
    a.raw(0xAC)                # lodsb
    a.raw(0x08, 0xC0)         # or al, al
    a.jz_short('send_str_ret')
    a.call_near('send_char')
    a.jmp_short('send_str')   # loop (need short jump back)
    a.label('send_str_ret')
    a.raw(0xC3)                # ret

    # send_n: send CX bytes from DS:SI
    a.label('send_n')
    a.raw(0xE3)                # jcxz send_n_ret (skip if cx=0)
    a.fixups.append((a.pos(), 'send_n_ret', 'rel8'))
    a.raw(0x00)
    a.label('send_n_loop')
    a.raw(0xAC)                # lodsb
    a.call_near('send_char')
    a.raw(0xE2)                # loop send_n_loop
    # Need relative offset back to send_n_loop
    a.fixups.append((a.pos(), 'send_n_loop', 'rel8'))
    a.raw(0x00)
    a.label('send_n_ret')
    a.raw(0xC3)                # ret

    # show_file: open file at DS:DX, send contents, close. Sends "(not found)" if missing.
    a.label('show_file')
    a.raw(0xB4, 0x3D)         # mov ah, 3Dh (open file)
    a.raw(0xB0, 0x00)         # mov al, 0 (read only)
    a.raw(0xCD, 0x21)         # int 21h
    a.jc_short('file_not_found')

    # AX = file handle
    a.raw(0x89, 0xC3)         # mov bx, ax (handle)

    a.label('read_loop')
    a.raw(0xB4, 0x3F)         # mov ah, 3Fh (read file)
    # BX already has handle
    a.raw(0xB9, 0x01, 0x00)   # mov cx, 1 (read 1 byte)
    a.raw(0xBA)                # mov dx, file_buf
    a.fixups.append((a.pos(), 'file_buf', 'rel16_abs'))
    a.dw(0)
    a.raw(0xCD, 0x21)         # int 21h
    a.jc_short('close_file')  # error
    a.raw(0x09, 0xC0)         # or ax, ax
    a.jz_short('close_file')  # EOF

    # Send the byte
    a.raw(0xA0)                # mov al, [file_buf]
    a.fixups.append((a.pos(), 'file_buf', 'rel16_abs'))
    a.dw(0)
    # Convert LF to CRLF for display
    a.raw(0x3C, 0x0A)         # cmp al, 0Ah
    a.jne_short('not_lf')
    a.raw(0xB0, 0x0D)         # mov al, CR
    a.call_near('send_char')
    a.raw(0xB0, 0x0A)         # mov al, LF
    a.label('not_lf')
    a.call_near('send_char')
    a.jmp_short('read_loop')

    a.label('close_file')
    a.raw(0xB4, 0x3E)         # mov ah, 3Eh (close file)
    a.raw(0xCD, 0x21)         # int 21h
    # Send CRLF after file
    a.raw(0xBE)
    a.fixups.append((a.pos(), 'msg_crlf', 'rel16_abs'))
    a.dw(0)
    a.call_near('send_str')
    a.raw(0xC3)                # ret

    a.label('file_not_found')
    a.raw(0xBE)
    a.fixups.append((a.pos(), 'msg_notfound', 'rel16_abs'))
    a.dw(0)
    a.call_near('send_str')
    a.raw(0xC3)                # ret

    # ===== Data =====

    a.label('msg_fossil')
    a.db("FOSSIL driver detected!\r\n", 0)

    a.label('msg_bios')
    a.db("No FOSSIL - using BIOS serial\r\n", 0)

    a.label('msg_header')
    a.db("============================================\r\n"
         "  DirtyFork Test Door v1.0\r\n"
         "============================================\r\n", 0)

    a.label('msg_cmdline')
    a.db("Command line:", 0)

    a.label('msg_crlf')
    a.db("\r\n", 0)

    a.label('msg_doorsys')
    a.db("--- C:\\DOOR.SYS ---\r\n", 0)

    a.label('msg_door32')
    a.db("--- C:\\DOOR32.SYS ---\r\n", 0)

    a.label('msg_notfound')
    a.db("(not found)\r\n", 0)

    a.label('msg_echo')
    a.db("\r\nEcho test - type text, Enter for newline, Q to quit\r\n", 0)

    a.label('msg_bye')
    a.db("\r\nGoodbye from Test Door!\r\n", 0)

    a.label('fn_doorsys')
    a.db("C:\\DOOR.SYS", 0)

    a.label('fn_door32')
    a.db("C:\\DOOR32.SYS", 0)

    a.label('file_buf')
    a.db(0)

    # Fix up absolute addresses (add 100h for .COM origin)
    # We stored these as 'rel16_abs' fixup type
    final_fixups = []
    for offset, label, ftype in a.fixups:
        if ftype == 'rel16_abs':
            target = a.labels[label] + 0x100  # .COM files load at CS:0100h
            struct.pack_into('<H', a.code, offset, target)
        else:
            final_fixups.append((offset, label, ftype))
    a.fixups = final_fixups

    return a.build()


if __name__ == "__main__":
    com = generate()
    outpath = "TESTDOOR.COM"
    with open(outpath, "wb") as f:
        f.write(com)
    print(f"Generated {outpath} ({len(com)} bytes)")
