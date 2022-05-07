import sys
import fileinput


def read_data():
    """
    コマンドライン引数の一番目で指定されたファイルから読み取り、一行ずつリストにして返す。
    コマンドライン引数が指定されなかった場合は、usageを表示してプログラムを終了する。
    """
    data = []
    for line in fileinput.input(encoding="utf-8"):
        s = line.strip()
        if not s:
            if fileinput.isstdin():
                break
            else:
                continue
        data.append(s)
    return data


def preproc(line):
    """
      一行の命令を命令名と引数の列に分解する。
      引数はカンマ区切りで分割され、前から順番にargsに入る。
      d(Rb)の形式のものは、d,Rbの順でargsに入る。
    """
    head, tail = "", ""
    for i in range(len(line)):
        if line[i] == " ":
            tail = line[i + 1 :]
            break
        head += line[i]
    cmd = head.upper()
    tmp = [s.strip() for s in tail.split(",") if not s == ""]
    args = []
    for i in range(len(tmp)):
        if "(" in tmp[i] and ")" in tmp[i]:
            a = tmp[i][: tmp[i].find("(")].strip()
            b = tmp[i][tmp[i].find("(") + 1 : tmp[i].find(")")].strip()
            try:
                args.append(int(a))
                args.append(int(b))
            except Exception:
                raise ValueError
        else:
            try:
                args.append(int(tmp[i]))
            except Exception:
                raise ValueError
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
    for i in range(len(data)):
        cmd, args = "", []
        try:
            cmd, args = preproc(data[i])
        except ValueError:
            print(str(i + 1) + "行目: 命令の引数が不正です", file=sys.stderr)
            exit(1)
        try:
            if cmd == "ADD":
                result.append(
                    "11"
                    + to_binary(args[1], 3)
                    + to_binary(args[0], 3)
                    + "0000"
                    + "0000"
                )
            elif cmd == "SUB":
                result.append(
                    "11"
                    + to_binary(args[1], 3)
                    + to_binary(args[0], 3)
                    + "0001"
                    + "0000"
                )
            elif cmd == "AND":
                result.append(
                    "11"
                    + to_binary(args[1], 3)
                    + to_binary(args[0], 3)
                    + "0010"
                    + "0000"
                )
            elif cmd == "OR":
                result.append(
                    "11"
                    + to_binary(args[1], 3)
                    + to_binary(args[0], 3)
                    + "0011"
                    + "0000"
                )
            elif cmd == "XOR":
                result.append(
                    "11"
                    + to_binary(args[1], 3)
                    + to_binary(args[0], 3)
                    + "0100"
                    + "0000"
                )
            elif cmd == "CMP":
                result.append(
                    "11"
                    + to_binary(args[1], 3)
                    + to_binary(args[0], 3)
                    + "0101"
                    + "0000"
                )
            elif cmd == "MOV":
                result.append(
                    "11"
                    + to_binary(args[1], 3)
                    + to_binary(args[0], 3)
                    + "0110"
                    + "0000"
                )
            elif cmd == "SLL":
                result.append(
                    "11"
                    + "000"
                    + to_binary(args[0], 3)
                    + "1000"
                    + to_binary(args[1], 4)
                )
            elif cmd == "SLR":
                result.append(
                    "11"
                    + "000"
                    + to_binary(args[0], 3)
                    + "1001"
                    + to_binary(args[1], 4)
                )
            elif cmd == "SRL":
                result.append(
                    "11"
                    + "000"
                    + to_binary(args[0], 3)
                    + "1010"
                    + to_binary(args[1], 4)
                )
            elif cmd == "SRA":
                result.append(
                    "11"
                    + "000"
                    + to_binary(args[0], 3)
                    + "1011"
                    + to_binary(args[1], 4)
                )
            elif cmd == "IN":
                result.append("11" + "000" + to_binary(args[0], 3) + "1100" + "0000")
            elif cmd == "OUT":
                result.append("11" + to_binary(args[0], 3) + "000" + "1101" + "0000")
            elif cmd == "HLT":
                result.append("11" + "000" + "000" + "1111" + "0000")
            elif cmd == "LD":
                result.append(
                    "00"
                    + to_binary(args[0], 3)
                    + to_binary(args[2], 3)
                    + to_binary(args[1], 8, signed=True)
                )
            elif cmd == "ST":
                result.append(
                    "01"
                    + to_binary(args[0], 3)
                    + to_binary(args[2], 3)
                    + to_binary(args[1], 8, signed=True)
                )
            elif cmd == "LI":
                result.append(
                    "10"
                    + "000"
                    + to_binary(args[0], 3)
                    + to_binary(args[1], 8, signed=True)
                )
            elif cmd == "B":
                result.append("10" + "100" + "000" + to_binary(args[0], 8, signed=True))
            elif cmd == "BE":
                result.append("10" + "111" + "000" + to_binary(args[0], 8, signed=True))
            elif cmd == "BLT":
                result.append("10" + "111" + "001" + to_binary(args[0], 8, signed=True))
            elif cmd == "BLE":
                result.append("10" + "111" + "010" + to_binary(args[0], 8, signed=True))
            elif cmd == "BNE":
                result.append("10" + "111" + "011" + to_binary(args[0], 8, signed=True))
            else:
                print(str(i + 1) + "行目:コマンド名が正しくありません", file=sys.stderr)
                exit(1)
        except ValueError as e:
            print(str(i + 1) + "行目 " + str(e) + ": 値の大きさが不正です", file=sys.stderr)
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