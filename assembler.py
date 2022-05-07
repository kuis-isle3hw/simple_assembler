import sys
import fileinput
import re


def read_data():
    """
    コマンドライン引数の一番目で指定されたファイルから読み取り、一行ずつリストにして返す。
    コマンドライン引数が指定されなかった場合は、標準入力を読み取る。
    """
    data = []
    for line in fileinput.input(encoding="utf-8"):
        s = line.strip()
        data.append(s)
        if not s and fileinput.isstdin():
                break # 標準入力のとき空行があったら終了
    return data


def preproc(line):
    """
      一行の命令を命令名と引数の列に分解する。
      引数は英数字以外の文字で分割され、前から順番にargsに入る。
      d(Rb)の形式のものは、d,Rbの順でargsに入る。
    """
    if "//" in line:
        line = line[:line.find("//")]
    head, *tail = re.findall(r"[a-zA-Z]+|[-+]?\d+", line)
    cmd = head.upper()
    args = []
    for i in tail:
        try:
            args.append(int(i))
        except Exception:
            raise ValueError(i)
    return cmd, args


def to_binary(num, digit, signed=False):
    """
      integerを指定された桁数(digit)の二進数に変換する。
      signed=Falseの場合は0埋めされ、signed=Trueの場合は二の補数表示になる。
    """
    if signed:
        if not -(2 ** (digit - 1)) <= num < 2 ** (digit - 1):
            raise ValueError(num)
        return format(num & (2 ** digit - 1), "0" + str(digit) + "b")
    else:
        if not 0 <= num < 2 ** digit:
            raise ValueError(num)
        return format(num, "0" + str(digit) + "b")


def assemble(data):
    result = []
    inst = { # 引数の数が多すぎるときに例外を発生させるため
        "ADD": lambda rd, rs:
            "11" + to_binary(rs, 3) + to_binary(rd, 3) + "0000" + "0000",
        "SUB": lambda rd, rs:
            "11" + to_binary(rs, 3) + to_binary(rd, 3) + "0001" + "0000",
        "AND": lambda rd, rs:
            "11" + to_binary(rs, 3) + to_binary(rd, 3) + "0010" + "0000",
        "OR": lambda rd, rs:
            "11" + to_binary(rs, 3) + to_binary(rd, 3) + "0011" + "0000",
        "XOR": lambda rd, rs:
            "11" + to_binary(rs, 3) + to_binary(rd, 3) + "0100" + "0000",
        "CMP": lambda rd, rs:
            "11" + to_binary(rs, 3) + to_binary(rd, 3) + "0101" + "0000",
        "MOV": lambda rd, rs:
            "11" + to_binary(rs, 3) + to_binary(rd, 3) + "0110" + "0000",
        "SLL": lambda rd, d:        
            "11" + "000" + to_binary(rd, 3) + "1000" + to_binary(d, 4),
        "SLR": lambda rd, d:        
            "11" + "000" + to_binary(rd, 3) + "1001" + to_binary(d, 4),
        "SRL": lambda rd, d:        
            "11" + "000" + to_binary(rd, 3) + "1010" + to_binary(d, 4),
        "SRA": lambda rd, d:        
            "11" + "000" + to_binary(rd, 3) + "1011" + to_binary(d, 4),
        "IN": lambda rd: 
            "11" + "000" + to_binary(rd, 3) + "1100" + "0000",
        "OUT": lambda rs:
            "11" + to_binary(rs, 3) + "000" + "1101" + "0000",
        "HLT": lambda:
            "11" + "000" + "000" + "1111" + "0000",
        "LD": lambda ra, d, rb:
            "00" + to_binary(ra, 3) + to_binary(rb, 3) + to_binary(d, 8, True),
        "ST": lambda ra, d, rb:
            "01" + to_binary(ra, 3) + to_binary(rb, 3) + to_binary(d, 8, True),
        "LI": lambda rb, d:
            "10" + "000" + to_binary(rb, 3) + to_binary(d, 8, signed=True),
        "B": lambda d:
            "10" + "100" + "000" + to_binary(d, 8, signed=True),
        "BE": lambda d:
            "10" + "111" + "000" + to_binary(d, 8, signed=True),
        "BLT": lambda d:
            "10" + "111" + "001" + to_binary(d, 8, signed=True),
        "BLE": lambda d:
            "10" + "111" + "010" + to_binary(d, 8, signed=True),
        "BNE": lambda d:
            "10" + "111" + "011" + to_binary(d, 8, signed=True)
    }
    for i, line in enumerate(data):
        if not line or line.startswith("//"):
            continue
        cmd, args = "", []
        try:
            cmd, args = preproc(data[i])
        except ValueError as e:
            print(str(i + 1) + "行目: 命令の引数が不正です", e, file=sys.stderr)
            exit(1)
        try:
            if cmd in inst:
                result.append(inst[cmd](*args))
            elif cmd.isdigit() or (cmd[0] == "-" and cmd[1:].isdigit()):
                result.append(to_binary(int(cmd), 16, signed=True))
            else:
                print(str(i + 1) + "行目:コマンド名が正しくありません", file=sys.stderr)
                exit(1)
        except ValueError as e:
            print(str(i + 1) + "行目 " + str(e) + ": 値の大きさが不正です", file=sys.stderr)
            exit(1)
        except TypeError as e:
            print(str(i + 1) + "行目 : 引数の数が不正です", e, file=sys.stderr)
            exit(1)
    return result


def write_result(result):
    """
      アセンブルした二進数のリストを書き込む
      書き込み先は、コマンドライン引数によって指定された場合はそのファイル、
      されなかった場合は標準出力
      ワード幅は16,ワード数は256としている
      DATA_RADIXは二進数、ADDRESS_RADIXはDECとしているが
      HEXのほうがよいか？
    """
    if len(sys.argv) >= 3:
        fout = open(sys.argv[2], mode="w")
        fout.write("WIDTH=16;\n")
        fout.write("DEPTH=256;\n")
        fout.write("ADDRESS_RADIX=DEC;\n")
        fout.write("DATA_RADIX=BIN;\n")
        fout.write("CONTENT BEGIN\n")
        for i in range(len(result)):
            fout.write("\t" + str(i) + " : " + result[i] + ";\n")
        fout.write("END;\n")
        fout.close()
    else:
        print("WIDTH=16;")
        print("DEPTH=256;")
        print("ADDRESS_RADIX=DEC;")
        print("DATA_RADIX=BIN;")
        print("CONTENT BEGIN")
        for i in range(len(result)):
            print("\t" + str(i) + " : " + result[i] + ";")
        print("END;")

def main():
    data = read_data()
    result = assemble(data)
    write_result(result)

if __name__ == "__main__":
    main()