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
        mcu = Emulator()
        # Random stack-pointer far away
        mcu.set_sp(0xA000)

        ad_bw_as = 0b1011
        src = 0 # operand next word in memory
        dst = 1 # address is SP + next word in memory
        val = 0x1337
        sp_offset = 0

        write_word(0x0000, mcu.memspace,
                   (Instructions.MOV[0]
                    | 0x0000 # src == 0
                    | (ad_bw_as << 4)
                    | dst))
        write_word(0x0002, mcu.memspace, val)
        write_word(0x0004, mcu.memspace, sp_offset)

        mcu.pc = 0
        mcu.exec_instruction()

        self.assertEquals(mcu.read_stack(sp_offset), val)

    def test_sub(self):
        mcu = Emulator()
        # Random stack-pointer far away
        mcu.set_sp(0xA000)

        ad_bw_as = 0b1001
        src = 3 # operand const 1 (as == 01)
        dst = 1 # address is SP + next word in memory
        sp_offset = 1 # next word in memory

        initial_val = 0x1337
        mcu.write_stack(sp_offset, initial_val)

        write_word(0x0000, mcu.memspace,
                   (Instructions.SUB[0]
                    | (src << 8)
                    | (ad_bw_as << 4)
                    | dst))
        write_word(0x0002, mcu.memspace, sp_offset)

        mcu.pc = 0
        mcu.exec_instruction()

        self.assertEquals(mcu.read_stack(sp_offset), initial_val - 1)

    def test_tst(self):
        # TST is same as CMP

        mcu = Emulator()
        # Random stack-pointer far away
        mcu.set_sp(0xA000)

        ad_bw_as = 0b1000
        src = 3 # operand const 0 (as == 00)
        dst = 1 # address is SP + next word in memory
        sp_offset = 0 # next word in memory

        write_word(0x0000, mcu.memspace,
                   (Instructions.CMP[0]
                    | (src << 8)
                    | (ad_bw_as << 4)
                    | dst))
        write_word(0x0002, mcu.memspace, sp_offset)

        # Write 123 to stack location, CMP should fail
        mcu.write_stack(sp_offset, 123)
        mcu.pc = 0
        mcu.exec_instruction()
        self.assertFalse(mcu.get_z())

        mcu.write_stack(sp_offset, 0)
        mcu.pc = 0
        mcu.exec_instruction()
        self.assertTrue(mcu.get_z())

    def test_jmp(self):
        mcu = Emulator()

        jmp_offset = 123

        write_word(0x0000, mcu.memspace,
                   (Instructions.JMP[0] | jmp_offset))

        mcu.pc = 0
        mcu.exec_instruction()

        self.assertEquals(mcu.pc, 2*jmp_offset + 2)


if __name__ == '__main__':
    unittest.main()
