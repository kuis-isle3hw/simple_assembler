import sys
import fileinput
import re
import argparse


def read_data(infile):
    """
    コマンドライン引数の一番目で指定されたファイルから読み取り、一行ずつリストにして返す。
    コマンドライン引数が指定されなかった場合は、標準入力を読み取る。
    """
    if not infile:
        infile = []
    data = []
    for line in fileinput.input(files=infile, encoding="utf-8"):
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
    """
      下処理された cmd と args の列を受け取り, 2進数の命令列を返す
      それぞれの cmd に対応した関数に args を渡すことで変換を行う
      命令を追加するときは inst に関数を追加する
    """
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
            elif cmd.isdigit() or (cmd[0] == "-" and cmd[1:].isdigit()): # 命令ではない値
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

def format_result(result, address_radix=10, data_radix=10,
                  width=16, depth=4096, fill=0, **kwargs):
    """
      アセンブルした二進数のリストを適当な形式に整えたものを返す
      アドレスの基数, データの基数をそれぞれ 2, 10, 16 から選ぶことができる
      ワード幅やメモリの語数を指定することができる
      ただし命令長を16ビットとしてアセンブリしているのでワード幅を変更すると正しい結果が得られないことがある
      命令を書き終えた残りのメモリに書き込む値を指定することができる
    """
    radix = {
        2: ("BIN", "b"),
        10: ("DEC", "d"),
        16: ("HEX", "x")
    }
    rdx_a, fmt_a = radix[address_radix]
    rdx_d, fmt_d = radix[data_radix]
    
    header = f"""WIDTH={width};
DEPTH={depth};
ADDRESS_RADIX={rdx_a};
DATA_RADIX={rdx_d};
CONTENT BEGIN"""
    
    if address_radix == 10: # 基数が10のとき0埋めしない
        padding_a = 0
    else: 
        padding_a = len(f"{depth-1 : {fmt_a}}")
    if data_radix == 10:
        padding_d = 0
    else: 
        padding_d = len(f"{2**width-1 : {fmt_d}}")

    formatted = [header]
    for i, bin_inst in enumerate(result):
        if address_radix == 10:
            address = i
        else:
            address = f"{i : 0{padding_a}{fmt_a}}"
        if data_radix == 10:
            if bin_inst[0] == "1":
                inst = str(int(bin_inst, 2) - 2**width)
            else:
                inst = str(int(bin_inst, 2))
        else:
            inst = f"{int(bin_inst, 2) : 0{padding_d}{fmt_d}}"
        formatted.append(f"{address} : {inst};")
    formatted.append(
        f"[{len(result): 0{padding_a}{fmt_a}} ..{depth-1: 0{padding_a}{fmt_a}}] : {fill: 0{padding_d}{fmt_d}};")
    formatted.append("END;")

    return "\n".join(formatted)

def write_result(result, output = None, **kwargs):
    """
      アセンブルした二進数のリストを書き込む
      書き込み先は、コマンドライン引数によって指定された場合はそのファイル、
      されなかった場合は標準出力
    """
    s = format_result(result, **kwargs)
    if output:
        try:
            with open(output, "w") as f:
                f.write(s)
                print(f"{output} に書き込みました")
        except Exception as e:
            print(f"ファイル {output} を開けなかったので標準出力に出力します" , e, file=sys.stderr)
            print(s)
    else:
        print(s)

def main():
    parser = argparse.ArgumentParser(description="SIMPLEアセンブラ")
    parser.add_argument("input", help="入力ファイル (デフォルト: 標準入力)", nargs="?")
    parser.add_argument("output", help="出力ファイル (デフォルト: 標準出力)", nargs="?")
    parser.add_argument("-d", "--depth", help="ワード数 (デフォルト: 4096)", type=int, nargs="?", default=4096)
    parser.add_argument("-ar", "--address_radix", help="アドレスの基数 (デフォルト: 10)", type=int, nargs="?", default=10, choices=[2, 10, 16])
    parser.add_argument("-dr", "--data_radix", help="データの基数 (デフォルト: 10)", type=int, nargs="?", default=10, choices=[2, 10, 16])
    parser.add_argument("-f", "--fill", help="空きメモリに埋める数 (デフォルト: 0)", type=int, nargs="?", default=0)
    args = parser.parse_args()

    data = read_data(args.input)
    result = assemble(data)
    write_result(result, **vars(args)) # 全部渡す

if __name__ == "__main__":
    main()