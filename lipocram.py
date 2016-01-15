#!/usr/bin/env python

import sys
import macholib.MachO
import os
import struct

class lipocram():

    def __init__(self, binary, data):
        self.binary = binary
        self.data = data
        self.fat_hdrs = {}
        
        if self.read_file():
            print "[*] Complete"

    def read_file(self):
        # this is dumb machO.machO.machO.idk.maybe seriously... 
        with open(self.binary, 'r') as f:
            magic_header = f.read(4)
        #self.aFile = macholib.MachO.MachO(self.binary)
        if magic_header == "\xCA\xFE\xBA\xBE":
            self.check_padding()
        else:
            print "[!] Not a Fat file"
            return False

    def check_padding(self):
        print "[*] Checking padding size against payload"
        self.size_of_data = os.stat(self.data).st_size
        # find size of padding
        with open(self.binary, 'r+b') as self.bin:
            self.bin.read(4)
            ArchNo = struct.unpack(">I", self.bin.read(4))[0]
            for arch in range(ArchNo):
                self.fat_hdrs[arch] = self.fat_header()
            self.end_fat_hdr = self.bin.tell()
        self.size_of_first_padding = self.fat_hdrs[0]['Offset']
        if self.size_of_first_padding - 400 > self.size_of_data:
            #write data
            self.start_offset = (self.size_of_first_padding - self.size_of_data) / 2 - self.end_fat_hdr
            self.size_of_new_padding = self.size_of_first_padding
            print "[*] New data location in Fat File", hex(self.start_offset)
            self.write_data()
        else:
            # extend data
            self.extend_padding()
            self.start_offset = (self.size_of_new_padding - self.size_of_data) / 2  - self.end_fat_hdr
            print "[*] New data location in Fat File", hex(self.start_offset)
            # write data
            self.write_data()
            self.fix_up_header()

    def extend_padding(self):
        print "[*] Finding page aligned new offset for storage area"
        self.multiple = 1
        while True:
            self.size_of_new_padding = self.size_of_first_padding * self.multiple
            if self.size_of_new_padding - 400 > self.size_of_data:
                break
            else:
                self.multiple += 1
        print "[*] Size of new padding", hex(self.size_of_new_padding)

    def write_data(self):
        print "[*] Writing", self.data, "to FAT file"
        with open(self.binary, 'r+b') as self.bin:
            temphdr = self.bin.read(self.end_fat_hdr)
            self.bin.seek(self.size_of_first_padding, 0)
            tempbin = self.bin.read()
            self.bin.seek(0,0)
            self.bin.write(temphdr)
            self.bin.write("\x00" * (self.size_of_new_padding - self.end_fat_hdr))
            self.bin.seek(self.start_offset, 0)
            self.bin.write(open(self.data, 'r').read())
            self.bin.seek(self.size_of_new_padding, 0)
            self.bin.write(tempbin)

    def fix_up_header(self):
        print "[*] Fixing up the FAT Headers"
        # typically offsets in universal binaries are equal
        with open(self.binary, 'r+b') as self.bin:
            for arch in self.fat_hdrs:
                #since we are doing the first one, we can continue
                self.bin.seek(self.fat_hdrs[arch]['OffsetLOC'], 0)
                self.bin.write(struct.pack(">I", self.fat_hdrs[arch]['Offset'] + (self.size_of_first_padding* self.multiple) - self.size_of_first_padding))

    def fat_header(self):
        header = {}
        header["CPU Type"] = struct.unpack(">I", self.bin.read(4))[0]
        header["CPU SubType"] = struct.unpack(">I", self.bin.read(4))[0]
        header["OffsetLOC"] = self.bin.tell()
        header["Offset"] = struct.unpack(">I", self.bin.read(4))[0]
        header["Size"] = struct.unpack(">I", self.bin.read(4))[0]
        header["Align"] = struct.unpack(">I", self.bin.read(4))[0]
        return header

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "Usage:", sys.argv[0], "Fatfile", "DataToCram"
        sys.exit(-1)
    lipocram(sys.argv[1], sys.argv[2])
