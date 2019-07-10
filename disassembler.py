#!/usr/bin/env python3
"""
This is a simple program which converts the nand2tetris book's Hack machine language back into hack assembly.
Note that the retranslation won't be 1-1, because label information is missing from the machine code.
This is based on my assembler implementation for chapter 6.
"""

import os
import sys


class ParserError(BaseException):
    pass


class Instruction(object):
    def __init__(self, instruction_string):
        self.instruction_string = instruction_string

    def validate(self):
        """
        Ensure that the instruction contains only valid characters
        """
        for char in self.instruction_string:
            if char != "0" and char != "1":
                msg = "Invalid character {}".format(char)
                raise ParserError(msg)
        if len(self.instruction_string) != 16:
            raise ParserError("Invalid instruction length: {}. Instructions must be exactly 16 characters long.".format(
                len(self.instruction_string)))

    def parse(self):
        """
        Parses a binary instruction into it's type and fields.
        """
        self.validate()
        # Determine the type of command by looking at the first character
        # If it's a 0 it's an A-command, otherwise it's a C-command.
        command = ""
        if self.instruction_string[0] == "0":
            command = self.gen_a_command()
        else:
            command = self.gen_c_command()
        return command

    def gen_a_command(self):
        # Because A-commands are prefixed with a 0, we only need to convert them from String to binary to decimal.
        val = int(self.instruction_string, 2)
        comment = ""
        # Values can only be positive per the spec, if isn't we screwed up
        assert val >= 0, "A-command value must not be negative"

        # Replace 0x4000 and 0x6000 with SCREEN/KBD
        if val == 0x4000:
            val = "SCREEN"
        elif val == 0x6000:
            val = "KBD"
        # Replace 0-15 w/ with virtual register labels R0-R15
        elif val >= 0 and val < 16:
            val = "R{}".format(val)
            # Inject AKA comments for ambiguous virtual register labels SP, LCL, ARG, THIS, and THAT (also assigned to R0-R4)
            if val == "R0":
                comment = "AKA @SP"
            elif val == "R1":
                comment = "AKA @LCL"
            elif val == "R2":
                comment = "AKA @ARG"
            elif val == "R3":
                comment = "AKA @THIS"
            elif val == "R4":
                comment = "AKA @THAT"

        if comment == "":
            return "@{}".format(val)
        else:
            return "@{} // {}".format(val, comment)

    def gen_c_command(self):
        """
        Converts the instruction to a C-command.
        """

        # Decode each bit
        # comp-related
        # For the sake of readability, comp bits are not decoded.
        # Instead, they're used raw.
        # The lines below are for reference only,
        # listed in the order of their bit's occurrences.
        # use_m
        # zx
        # nx
        # zy
        # ny
        # f
        # not_output

        # dest-related
        dest_a = (self.instruction_string[10] == "1")
        dest_d = (self.instruction_string[11] == "1")
        dest_m = (self.instruction_string[12] == "1")
        # jmp-related
        jump_less = (self.instruction_string[13] == "1")
        jump_equal = (self.instruction_string[14] == "1")
        jump_greater = (self.instruction_string[15] == "1")

        # Generate the appropriate mnemonics
        # See the tables on page 87, this is basically just a transcription
        # First, comp
        # We simply go through the table, row-by-row
        # and compare the relevant slice of the instruction to each row.
        comp_mnemonic = ""
        comp_slice = self.instruction_string[3:10]

        if comp_slice == "0101010":
            comp_mnemonic = "0"
        if comp_slice == "1101010":
            raise ParserError(
                "Invalid comp instruction: {}".format(comp_slice))

        if comp_slice == "0111111":
            comp_mnemonic = "1"
        if comp_slice == "1111111":
            raise ParserError(
                "Invalid comp instruction: {}".format(comp_slice))

        if comp_slice == "0111010":
            comp_mnemonic = "-1"
        if comp_slice == "1111010":
            raise ParserError(
                "Invalid comp instruction: {}".format(comp_slice))

        if comp_slice == "0001100":
            comp_mnemonic = "D"
        if comp_slice == "1001100":
            raise ParserError(
                "Invalid comp instruction: {}".format(comp_slice))

        if comp_slice == "0110000":
            comp_mnemonic = "A"
        if comp_slice == "1110000":
            comp_mnemonic = "M"

        if comp_slice == "0001101":
            comp_mnemonic = "!D"
        if comp_slice == "1001101":
            raise ParserError(
                "Invalid comp instruction: {}".format(comp_slice))

        if comp_slice == "0110001":
            comp_mnemonic = "!A"
        if comp_slice == "1110001":
            comp_mnemonic = "!M"

        if comp_slice == "0001111":
            comp_mnemonic = "-D"
        if comp_slice == "1001111":
            raise ParserError(
                "Invalid comp instruction: {}".format(comp_slice))

        if comp_slice == "0110011":
            comp_mnemonic = "-A"
        if comp_slice == "1110011":
            comp_mnemonic = "-M"

        if comp_slice == "0011111":
            comp_mnemonic = "D+1"
        if comp_slice == "1011111":
            raise ParserError(
                "Invalid comp instruction: {}".format(comp_slice))

        if comp_slice == "0110111":
            comp_mnemonic = "A+1"
        if comp_slice == "1110111":
            comp_mnemonic = "M+1"

        if comp_slice == "0001110":
            comp_mnemonic = "D-1"
        if comp_slice == "1001110":
            raise ParserError(
                "Invalid comp instruction: {}".format(comp_slice))

        if comp_slice == "0110010":
            comp_mnemonic = "A-1"
        if comp_slice == "1110010":
            comp_mnemonic = "M-1"

        if comp_slice == "0000010":
            comp_mnemonic = "D+A"
        if comp_slice == "1000010":
            comp_mnemonic = "D+M"

        if comp_slice == "0010011":
            comp_mnemonic = "D-A"
        if comp_slice == "1010011":
            comp_mnemonic = "D-M"

        if comp_slice == "0000111":
            comp_mnemonic = "A-D"
        if comp_slice == "1000111":
            comp_mnemonic = "M-D"

        if comp_slice == "0000000":
            comp_mnemonic = "D&A"
        if comp_slice == "1000000":
            comp_mnemonic = "D&M"

        if comp_slice == "0010101":
            comp_mnemonic = "D|A"
        if comp_slice == "1010101":
            comp_mnemonic = "D|M"

        # Then, dest
        dest_mnemonic = ""
        if dest_a:
            dest_mnemonic += "A"
        if dest_m:
            dest_mnemonic += "M"
        if dest_d:
            dest_mnemonic += "D"
        if dest_mnemonic != "":
            dest_mnemonic = dest_mnemonic + "="

        # Finally, jmp
        jmp_mnemonic = ""
        if not jump_less and not jump_equal and jump_greater:
            jmp_mnemonic = ";JGT"
        if not jump_less and jump_equal and not jump_greater:
            jmp_mnemonic = ";JEQ"
        if not jump_less and jump_equal and jump_greater:
            jmp_mnemonic = ";JGE"
        if jump_less and not jump_equal and not jump_greater:
            jmp_mnemonic = ";JLT"
        if jump_less and not jump_equal and jump_greater:
            jmp_mnemonic = ";JNE"
        if jump_less and jump_equal and not jump_greater:
            jmp_mnemonic = ";JLE"
        if jump_less and jump_equal and jump_greater:
            jmp_mnemonic = ";JMP"

        if comp_mnemonic == "":
            raise ParserError("Comp cannot be null")
        return "{}{}{}".format(dest_mnemonic, comp_mnemonic, jmp_mnemonic)


def main():
    # Read the machine code file
    if len(sys.argv) != 2:
        print("Usage: {0} Prog.hack".format(sys.argv[0]))
        sys.exit(1)

    if not os.path.exists(sys.argv[1]):
        print("File {0} does not exist".format(sys.argv[1]))
        sys.exit(1)

    hack_file = sys.argv[1]
    hack_lines = list()
    try:
        with open(hack_file, "r") as f:
            for line in f:
                hack_lines.append(line.rstrip())
    except IOError as error:
        sys.stderr.write(
            "{0}: Encountered error while trying to open file {1}: {2}".format(sys.argv[0], hack_file, error))
        sys.exit(1)

    # Translate line-by-line and dump to output file
    asm_file = sys.argv[1].replace(".hack", ".asm")
    asm_lines = list()
    for hack_line in hack_lines:
        asm_lines.append(Instruction(hack_line).parse())

    try:
        with open(asm_file, "w") as f:
            for line in asm_lines:
                f.write(line + "\n")
    except IOError as error:
        sys.stderr.write(
            "{0}: Encountered error while trying to open file {1}: {2}".format(sys.argv[0], hack_file, error))
        sys.exit(1)


if __name__ == "__main__":
    main()
