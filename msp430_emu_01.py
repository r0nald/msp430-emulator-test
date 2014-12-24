import array


# Need to implement:
# XOR.B, MOV.W, SUB.W, TST.W == CMP, JEQ, JMP
class Instructions:
    # (instruction code, bit-mask)
    # XXX _B and _W difference not taken into account
    # in the instruction and bit-masks here:
    XOR = (0xe000, 0xf000)
    MOV = (0x4000, 0xf000)
    SUB = (0x8000, 0xf000)
    CMP = (0x9000, 0xf000)
    JEQ = (0x2400, 0xfc00)
    JMP = (0x3C00, 0xfc00)


def is_instruction(instruction, word):
    return ((word ^ instruction[0]) & instruction[1]) == 0


def read_word(index, memspace):
    return memspace[index+1] << 8 | memspace[index]


def write_word(index, memspace, val):
    memspace[index+1] = 0xFF & (val >> 8)
    memspace[index] = 0xFF & val


def read_from_stack(offset, memspace, registers):
    sp = read_word(Registers.SP, registers)
    return read_word(sp + offset, memspace)


def write_to_stack(offset, memspace, registers, val):
    sp = read_word(Registers.SP, registers)
    return write_word(sp + offset, memspace, val)

def _raise_notimplemented(instruction):
    raise NotImplementedError('Instruction 0x%x not implemented'
                              % instruction)

class Registers:
    SP = 1
    SR = 2


def set_z(registers):
    Z_bit = 1
    val = read_word(Registers.SR, registers)
    val |= 1 << Z_bit
    write_word(Registers.SR, registers, val)


def clear_z(registers):
    Z_bit = 1
    val = read_word(Registers.SR, registers)
    val &= ~(1 << Z_bit)
    write_word(Registers.SR, registers, val)


def get_z(registers):
    Z_bit = 1
    return 0x1 & (read_word(Registers.SR, registers) >> Z_bit)


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
            self.src_val = read_word(self.pc + 2, self.memspace)
            self.is_src_in_mem = True
        else:
            _raise_notimplemented(self.instruction_word)

        if dst == 1:
            # stack pointer
            # next word contains SP offset
            offset = read_word(self.pc + 4, self.memspace) \
                if self.is_src_in_mem \
                else read_word(self.pc + 2, self.memspace)
            self._destination = (Destination.Memspace,
                                 read_word(Registers.SP,
                                           self.registers) + offset)
        elif dst == 2:
            dst_addr = read_word(self.pc
                                 + (4 if self.is_src_in_mem else 2),
                                 self.memspace)
            self._destination = (Destination.Memspace, dst_addr)
        else:
            _raise_notimplemented(self.instruction_word)

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
        if is_instruction(Instructions.MOV, self.instruction_word):
            write_word(self.operands.destination()[1], self.memspace,
                       self.operands.source_operand_val())
        elif is_instruction(Instructions.SUB, self.instruction_word):
            write_word(self.operands.destination()[1], self.memspace,
                       read_word(self.operands.destination()[1],
                                 self.memspace)
                       - self.operands.source_operand_val())
        elif is_instruction(Instructions.CMP, self.instruction_word):
            if read_word(self.operands.destination()[1],
                         self.memspace) \
                    == self.operands.source_operand_val():
                set_z(self.registers)
            else:
                clear_z(self.registers)
        elif is_instruction(Instructions.XOR, self.instruction_word):
            operand = self.operands.source_operand_val()
            dst_addr = self.operands.destination()[1]
            dst_val = read_word(dst_addr, self.memspace)
            write_word(dst_addr, self.memspace, dst_val ^ operand)
        else:
            _raise_notimplemented(self.instruction_word)


class JumpInstruction:
    def __init__(self, pc, memspace, registers):
        self.pc = pc
        self.memspace = memspace
        self.registers = registers
        self.instruction_word = read_word(pc, memspace)
        self._next_pc = None

    def execute(self):
        offset = (self.instruction_word & 0x03FF)
        if offset & (1<<9):
            offset = -(2**10) + offset

        if is_instruction(Instructions.JEQ, self.instruction_word):
            if get_z(self.registers):
                self._next_pc = self.pc + 2*offset + 2
            else:
                self._next_pc = self.pc + 2
        elif is_instruction(Instructions.JMP, self.instruction_word):
                self._next_pc = self.pc + 2*offset + 2
        else:
            _raise_notimplemented(self.instruction_word)

    def next_pc(self):
        return self._next_pc


class Emulator:
    def __init__(self):
        self.memspace = array.array('B', '\0' * 2 ** 16)
        self.registers = array.array('B', '\0' * 16)
        # TODO:
        self.pc = 0
        # self.set_sp()

    def exec_instruction(self):
        instruction_nibble = read_word(self.pc, self.memspace) & 0xF000
        if instruction_nibble == 0x1000:
            # single-operand instructions
            pass
        elif instruction_nibble in [0x2000, 0x3000]:
            # JMP instructions
            instruction_obj = JumpInstruction(self.pc,
                                              self.memspace,
                                              self.registers)
        elif instruction_nibble >= 0x4000:
            instruction_obj = DualOperandInstruction(self.pc,
                                                     self.memspace,
                                                     self.registers)
        instruction_obj.execute()
        self.pc = instruction_obj.next_pc()

    def write_stack(self, offset, val):
        write_to_stack(offset, self.memspace, self.registers, val)

    def read_stack(self, offset):
        return read_from_stack(offset, self.memspace, self.registers)

    def set_sp(self, sp):
        write_word(Registers.SP, self.registers, sp)

    def get_z(self):
        return get_z(self.registers)

    def set_z(self):
        set_z(self.registers)

    def clear_z(self):
        clear_z(self.registers)

    def run(self):
        while True:
            self.exec_instruction()
