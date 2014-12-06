import unittest
from msp430_emu_01 import *

class TestDualOperandInstructions(unittest.TestCase):
    def test_xor(self):
        mcu = Emulator()
        ad_bw_as = 0b1101
        dst_addr = 0x00A0
        write_word(0x0000, mcu.memspace,
            (Instructions.XOR[0] |
             0x0300 | # src == 3 <-> const 1
             (ad_bw_as << 4) |
             0x0002)) # destination addr in next word
        write_word(0x0002, mcu.memspace, dst_addr)

        mcu.pc = 0
        self.assertEquals(read_word(dst_addr, mcu.memspace), 0)

        mcu.exec_instruction()
        self.assertEquals(read_word(dst_addr, mcu.memspace), 1)
        self.assertEquals(mcu.pc, 0x0004)

        mcu.pc = 0
        mcu.exec_instruction()
        self.assertEquals(read_word(dst_addr, mcu.memspace), 0)
        self.assertEquals(mcu.pc, 0x0004)

    def test_mov(self):
        pass


if __name__ == '__main__':
    unittest.main()
