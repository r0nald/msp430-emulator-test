from msp430_emu_01 import Emulator, read_word
from intelhex import IntelHex
from StringIO import StringIO
import sys

hex_file_string = """
:20E000002A143F4000003F90010023283F4000003F9001001E283A4000003A8000003A50D5
:20E0200007005A09394000003C493D493E493F49C80CCB0D1C530D630F184B5B00184BD850
:20E040006B4B4B4B5B0600185B4B00004B131A83EB233F4000003F90000008243A40000058
:20E06000023C6A132A523A900000FB23281610012183B240805A5C01D2D30402D2E3020201
:20E08000B140102700009183000081930000F627FA3F034331400020B013B4E00C930224E7
:1CE0A000B01300E00C43B01370E0B013B8E032D01000FD3F1C4310010343FF3FC2
:02FFDA00AEE097
:02FFDC00AEE095
:02FFDE00AEE093
:02FFE000AEE091
:02FFE200AEE08F
:02FFE400AEE08D
:02FFE600AEE08B
:02FFE800AEE089
:02FFEC00AEE085
:02FFEE00AEE083
:02FFF000AEE081
:02FFF200AEE07F
:02FFF400AEE07D
:02FFF600AEE07B
:02FFF800AEE079
:02FFFA00AEE077
:02FFFC00AEE075
:02FFFE0094E08D
:00000001FF
"""

def led_status(mcu):
    PAOUT = 0x0202
    return mcu.memspace[PAOUT] & 1

def run_mcu(hex_code):
    mcu = Emulator()
    mcu.memspace[hex_code.minaddr():hex_code.maxaddr()+1] \
        = hex_code.tobinarray()

    # start of main function in memory:
    main_addr = 0xE070
    # we'll skip some initial instructions:
    skip_instructions = 12

    mcu.pc = main_addr + skip_instructions
    # is this pretty random SP?
    mcu.set_sp(0x1fb0)

    mcu_freq = 1 * (10**6)

    print_freq = 200

    for i in xrange(sys.maxint):
        if (i * print_freq) % mcu_freq == 0:
            t = 1.0 * i / mcu_freq
            print 't = %f LED %d' % (t, led_status(mcu))
        mcu.exec_instruction()

def main():
    if len(sys.argv) > 1:
        hex_code = IntelHex(sys.argv[1])
    else:
        hex_code = IntelHex(StringIO(hex_file_string))
    run_mcu(hex_code)

if __name__ == '__main__':
    main()
