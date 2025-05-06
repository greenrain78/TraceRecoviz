import os
import json
import re

log_dir = "./log"
output_dir = "./json_output"
os.makedirs(output_dir, exist_ok=True)

def extract_type(sig):
    if "::" in sig:
        return sig.split("::")[0]
    return sig.split(' ')[0] if ' ' in sig else sig

def parse_log_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    nodes = {}
    links = []
    time_counter = 0
    activation_stack = {}
    activation_boxes = []
    message_lengths = []

    for line in lines:
        line = line.strip()
        if not line or "[TRACE]" in line:
            continue

        match = re.match(r"\[(.*?)\] \[(CALL|RETURN)\] caller: \(ptr=(.*?)\) (.*?) => callee: \(ptr=(.*?)\) (.*)", line)
        if not match:
            continue

        testname, action, caller_ptr, caller_sig, callee_ptr, callee_sig = match.groups()

        caller_type = extract_type(caller_sig)
        callee_type = extract_type(callee_sig)
        caller_name = f"{caller_type}#{caller_ptr}"
        callee_name = f"{callee_type}#{callee_ptr}"

        if caller_ptr not in nodes:
            nodes[caller_ptr] = {
                "key": caller_ptr,
                "text": caller_name,
                "loc": f"{len(nodes)*200} 0",
                "size": f"{max(100, len(caller_name)*6)} 60",
                "isGroup": True,
                "duration": 0
            }
        if callee_ptr not in nodes:
            nodes[callee_ptr] = {
                "key": callee_ptr,
                "text": callee_name,
                "loc": f"{len(nodes)*200} 0",
                "size": f"{max(100, len(callee_name)*6)} 60",
                "isGroup": True,
                "duration": 0
            }

        if action == "CALL":
            activation_stack[callee_ptr] = activation_stack.get(callee_ptr, 0) + 1

            activation_boxes.append({
                "group": callee_ptr,
                "start": time_counter,
                "duration": 2
            })

            message_text = callee_sig

            links.append({
                "from": caller_ptr,
                "to": callee_ptr,
                "text": message_text,
                "time": time_counter,
                "activation": activation_stack.get(callee_ptr, 0)
            })

        elif action == "RETURN":
            ret_type = callee_sig.split(' ')[0]
            ret_value = callee_sig.split('=>')[-1].strip() if '=>' in callee_sig else ""
            message_text = f"{ret_value} : {ret_type}" if ret_value else f"(void) : {ret_type}"

            links.append({
                "from": callee_ptr,
                "to": caller_ptr,
                "text": message_text,
                "time": time_counter,
                "activation": activation_stack.get(callee_ptr, 0)
            })

            activation_stack[callee_ptr] = max(activation_stack.get(callee_ptr, 1) - 1, 0)

        message_lengths.append(len(message_text))
        time_counter += 2

    total_duration = time_counter + 2
    max_msg_length = max(message_lengths) if message_lengths else 25
    gap_x = max(200, max_msg_length * 8)

    for i, node in enumerate(nodes.values()):
        node["duration"] = total_duration
        node["loc"] = f"{i * gap_x} 0"

    return {
        "class": "go.GraphLinksModel",
        "nodeDataArray": list(nodes.values()),
        "linkDataArray": links + activation_boxes
    }

print("💡 Script started")

for filename in os.listdir(log_dir):
    if filename.endswith(".log"):
        print(f"Processing file: {filename}")
        filepath = os.path.join(log_dir, filename)
        result = parse_log_file(filepath)
        outpath = os.path.join(output_dir, filename.replace(".log", ".json"))
        with open(outpath, 'w') as out_f:
            json.dump(result, out_f, indent=2)
        print(f"✅ Converted {filename} -> {outpath}")

print("💡 Script finished")
