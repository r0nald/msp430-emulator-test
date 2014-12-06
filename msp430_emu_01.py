import array

# Need to implement:
# XOR.B, MOV.W, SUB.W, TST.W == CMP, JEQ, JMP
class Instructions:
    # (instruction code, bit-mask)
    # XXX _B and _W difference not taken into account
    # in the instruction and bit-masks here:
    XOR = (0xe000, 0xf000)
    MOV_W = (0x4000, 0xf000)
    SUB_W = (0x8000, 0xf000)
    CMP_W = (0x9000, 0xf000)
    JEQ = (0x2400, 0xff00)
    JMP = (0x3C00, 0xff00)


def read_word(index, memspace):
    return memspace[index+1] << 8 | memspace[index]


def write_word(index, memspace, val):
    memspace[index+1] = 0xFF & (val >> 8)
    memspace[index] = 0xFF & val


class Registers:
    SP = 1
    SR = 2


def set_z(registers):
    Z_bit = 1
    val = read_word(Registers.SR, registers)
    val |= 1<<Z_bit
    write_word(Registers.SR, registers, val)


def clear_z(registers):
    Z_bit = 1
    val = read_word(Registers.SR, registers)
    val &= ~(1<<Z_bit)
    write_word(Registers.SR, registers, val)


class Destination:
    Register = 0
    Memspace = 1


class DualOperands:
    def __init__(self, pc, memspace, registers):
        self.pc = pc
        self.memspace = memspace
        self.registers = registers
        self.instruction_word = read_word(pc, memspace)

        # Decide operands
        # Need to implement modes: As/Ad - 01/1, 11/1, 01/1, 00/1
        as_bits = (self.instruction_word & 0x0030) >> 4
        ad_bit = (self.instruction_word & 0x0080) >> 7
        src = (self.instruction_word & 0x0F00) >> 8
        dst = (self.instruction_word & 0x000F)

        self.src_val = None

        # If True, source operand or its address in following word
        self.is_src_in_mem = False

        if src == 3:
            # Operand is constant
            # With this we have covered instructions:
            # XOR.B, SUB.W, TST.W/CMP
            if as_bits == 0b11:
                self.src_val = -1
            else:
                self.src_val = as_bits
        elif as_bits == 0b11 and src == 0:
            # Immediate, source is in address given by next word
            self.src_val = read_word(self.pc + 2)
            self.is_src_in_mem = True
        else:
           raise NotImplementedError('Instruction 0x%x not implemented'
                                     % self.instruction_word)

        if dst == 1:
            # stack pointer
            # It could be that next word contains 0 for SP+0
            self._destination = (Destination.Memspace,
                                self.registers[Registers.SP])
        elif dst == 2:
            dst_addr = read_word(self.pc
                                 + (4 if self.is_src_in_mem else 2),
                                 self.memspace)
            self._destination = (Destination.Memspace, dst_addr)
        else:
           raise NotImplementedError('Instruction 0x%h not implemented'
                                     % self.instruction_word)

    def instruction_step(self):
        """ Next instruction should be found after how many bytes """
        if self.is_src_in_mem:
            return 2*3
        else:
            return 2*2

    def source_operand_val(self):
        return self.src_val

    def destination(self):
        """ Return (destination type, address/index) """
        return self._destination


class DualOperandInstruction:
    def __init__(self, pc, memspace, registers):
        self.pc = pc
        self.memspace = memspace
        self.registers = registers
        self.operands = DualOperands(pc, memspace, registers)
        self.instruction_word = self.operands.instruction_word

    def next_pc(self):
        return self.pc + self.operands.instruction_step()

    def execute(self):
        instruction = self.instruction_word & 0xF000

        if instruction == 0x4000:
            # MOV
            write_word(self.operands.destination()[1], self.memspace,
                       self.operands.source_operand_val())
        elif instruction == 0x8000:
            # SUB
            write_word(self.operands.destination()[1], self.memspace,
                       read_word(self.operands.destination()[1],
                                 self.memspace)
                       - self.operands.source_operand_val())
        elif instruction == 0x9000:
            # CMP/TST
            if read_word(self.operands.destination()[1],
                          self.memspace) \
                    == self.operands.source_operand_val():
                set_z(self.registers)
            else:
                clear_z(self.registers)
        elif instruction == 0xE000:
            # XOR
            operand = self.operands.source_operand_val()
            dst_addr = self.operands.destination()[1]
            dst_val = read_word(dst_addr, self.memspace)
            write_word(dst_addr, self.memspace, dst_val ^ operand)
        else:
           raise NotImplementedError('Instruction 0x%h not implemented'
                                     % self.instruction_word)

class Emulator:
    def __init__(self):
        self.memspace = array.array('B', '\0' * 2 ** 16)
        self.registers = array.array('B', '\0' * 16)
        # TODO:
        self.pc = 0

    def exec_instruction(self):
        instruction_nibble = read_word(self.pc, self.memspace) & 0xF000
        if instruction_nibble == 0x1000:
            # single-operand instructions
            pass
        elif instruction_nibble & 0xE == 0x2000:
            # JMP instructions
            pass
        elif instruction_nibble >= 0x8000:
            instruction_obj = DualOperandInstruction(self.pc,
                                                     self.memspace,
                                                     self.registers)
        instruction_obj.execute()
        self.pc = instruction_obj.next_pc()

    def run(self):
        while True:
            self.exec_instruction()
