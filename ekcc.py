import argparse, sys
import lexer, yacc, codeGen, binding
import yaml
import os
import time

def read_content(input_file):
    with open(input_file, 'r') as input:  
        content = input.read()
        return content

def write_to_file(output_file, content):
    if isinstance(output_file, str):
        with open(output_file, 'w') as output:  
            output.write(content)
    else:
        output_file.write(content)

parser = argparse.ArgumentParser(prog=sys.argv[0], 
                                 description='Compiler',
                                 usage="python3 ekcc.py [-h|-?] [-v] [-O] [-emit-ast|-emit-llvm] -o <output-file> <input-file> [-jit] [-dul] -it <inlining_threshold> [-lv] -ol <opt_level> -sl <size_level> [-sv]", 
                                 add_help=False)
parser.add_argument("-h", action="help", help="show this help message and exit")
parser.add_argument("-v", action="store_true", help="print information for debugging")
parser.add_argument("-O", action="store_true", help="enable optimization")
parser.add_argument("-emit-ast", action="store_true", default=False, help="generate AST")
parser.add_argument("-emit-llvm", action="store_true", default=False, help="generate LLVM IR")
parser.add_argument("-o", action="store", default=sys.stdout, help="set output file path")
parser.add_argument("input_file", help = "ek file to be compiled")
parser.add_argument("-jit", action="store_true", help = "use JIT")
parser.add_argument("-dul", action="store_true", help = "disable loop unrolling")
parser.add_argument("-it", action="store", default = 10, help = "the integer threshold for inlining one function into another")
parser.add_argument("-lv", action="store_true", help = "allow vectorizing loops")
parser.add_argument("-ol", action="store", default = 3, help = "general optimization level")
parser.add_argument("-sl", action="store", default = 2, help = "whether and how much to optimize for size, as an integer between 0 and 2")
parser.add_argument("-sv", action="store_true", help = "enable the SLP vectorizer")
args, undefined = parser.parse_known_args()

exitcode = 0

if args.emit_ast and args.emit_llvm:
    raise Exception("Cannot emit_ast and emit_llvm at the same time")
else:
    content = read_content(args.input_file)
    ast, err_message = yacc.parse(content)
    if err_message != None:
        print(err_message)
        print("exit code: "+str(1))
        sys.exit(1)
    if args.emit_ast:
        write_to_file(args.o,  yaml.dump(ast))
    print("######## Generating IR ########")
    start_time = time.time()
    mod = codeGen.generate_code(ast, undefined)
    print("######## Total Time: %s seconds ########" % (time.time() - start_time))
    print()
    optimization = [args.dul, args.it, args.lv, args.ol, args.sl, args.sv]
    mod = binding.compile_and_execute(mod, args.O, args.jit, optimization)
    if args.emit_llvm:
        if args.o != "exe":
            write_to_file(args.o, mod)
        elif not args.jit:
            write_to_file("temp.ll", mod)
            os.system("clang -c temp.ll -o temp.o")
            os.system("clang main.cpp temp.o -o exe")

print("exit code: "+str(exitcode))