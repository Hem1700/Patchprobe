# Headless Ghidra post-script for extracting pseudocode for a function name.
# Script args:
#   1) function_name
#   2) output_json_path
#   3) output_txt_path
#   4) timeout_sec (optional, currently informational)

import json

from ghidra.app.decompiler import DecompInterface


def _find_function(function_name):
    fm = currentProgram.getFunctionManager()
    funcs = fm.getFunctions(True)
    for f in funcs:
        name = f.getName()
        if name == function_name or name == "_" + function_name:
            return f
    return None


def _write(path, text):
    with open(path, "w") as fh:
        fh.write(text)


args = getScriptArgs()
if len(args) < 3:
    raise RuntimeError("expected args: <function_name> <output_json_path> <output_txt_path> [timeout_sec]")

function_name = args[0]
output_json_path = args[1]
output_txt_path = args[2]
timeout_sec = int(args[3]) if len(args) > 3 else 60

target = _find_function(function_name)
if target is None:
    payload = {
        "status": "function_not_found",
        "function_name": function_name,
        "prototype": None,
        "decompile_time_sec": 0,
    }
    _write(output_json_path, json.dumps(payload))
    _write(output_txt_path, "/* function not found */\n")
    print("function not found: " + function_name)
    exit()

iface = DecompInterface()
iface.openProgram(currentProgram)
res = iface.decompileFunction(target, timeout_sec, monitor)
pseudo = ""
prototype = str(target.getSignature())
status = "ok"
if res is not None and res.decompileCompleted():
    pseudo = res.getDecompiledFunction().getC()
else:
    status = "decompile_failed"
    pseudo = "/* decompile failed */\n"

payload = {
    "status": status,
    "function_name": function_name,
    "prototype": prototype,
    "decompile_time_sec": timeout_sec,
}
_write(output_json_path, json.dumps(payload))
_write(output_txt_path, pseudo)
print("decompiled: " + function_name)
