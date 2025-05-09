import re
import json

position_state = {
    "current_x": 480,
    "scale_x": 8,
    "margin": 10
}


def compute_loc(text, time=None, pos_state=None):
    x = pos_state["current_x"]
    # 텍스트 길이에 따라 x 증가
    pos_state["current_x"] += len(text) * pos_state["scale_x"] + pos_state["margin"]

    y = 0 if time is None else time * 20
    return f"{x} {y}"



def convert_to_gojs(lines):
    nodeDataArray = []
    linkDataArray = []
    activations = []
    fixtureClass = []
    destroyed_nodes = set()
    # test_name = ""
    # for line in lines:  
    #     #match = re.match(r"\[(\w+\.\w+)]", line)
    #     match = re.match(r"\[(.*?)\]", line)
    #     if match:
    #         test_name = match.group(1)
    #         print(f"test_name: {test_name}")
    #         break
    # 테스트 이름 추출 로직
    test_name = ""
    class_name = ""


    for line in lines:
        if "[CALL" in line or "[CTOR" in line or "[RETURN" in line or "[DTOR" in line:
            match = re.match(r"\[([^\]]+)\]", line)
            if match:
                test_name = match.group(1)

                if "[CTOR" in line or "[DTOR" in line:
                    class_match = re.search(r"(\w+)::\w+\(", line)
                    if class_match:
                        class_name = class_match.group(1)
                    else:
                        class_name = None
                break


    pattern = re.escape(test_name)
    # print(f"pattern: {pattern}")
    events = [line.strip() for line in lines if re.match(rf"\[{pattern}]", line)]
    #print(f"events: {events}")
    #events = [line.strip() for line in lines if re.match(r"\[" + test_name + r"\]", line)]
    # pattern = re.escape(test_name)
    #events = line.strip().split("\n")

    duration = len(events) * 2 + 4

    nodeDataArray.append({
        "key": "TestRunner",
        "text": "TestRunner",
        "isGroup": True,
        "loc": "0 0",
        "duration": duration
    })

    nodeDataArray.append({
        "key": test_name,
        "text": test_name + "",
        "isGroup": True,
        "loc": "180 0",
        "duration": duration - 1
    })

    nodeDataArray.append({
        "key": class_name,
        "text": class_name + "",
        "isGroup": True,
        "loc": "360 0",
        "duration": duration - 2
    })

    linkDataArray.append({
        "from": "TestRunner",
        "to": test_name + "",
        "text": "TestBody()",
        "time": 1
    })

    time_counter = 3
    node_keys = {"TestRunner", test_name + ""}
    current_x = 480

    call_stack = []
    recent_by_intent = {}
    instance_label_map = {}
    intent_map = {}
    
    call_activation_map = {}  # key: inst, value: start_time
    for idx, line in enumerate(events):
        match_call = re.match(
            rf"\[({test_name})]\s+\[CALL\s*\]\s+\((.*?)\)\s+([\w\s:*<>,]+)\s+([\w:<>~]+::\w+)\((.*?)\)(?:\s+(.*))?",
            line)
        match_return = re.match(
            rf"\[({test_name})]\s+\[RETURN\d*\] \((.*?)\)\s+([\w\s:*<>,]+)\s+([\w:<>~]+)\((.*?)\).*=>\s+(.*)",
            line)
        match_ctor_call = re.match(
            rf"\[({test_name})]\s+\[CTOR Call\s*\]\s+([\w:<>]+)::([\w:<>]+)\((.*?)\)",
            line)
        #print(f"match_ctor_call: {match_ctor_call}")
        #match_ctor_return = re.match()
        match_dtor_call = re.match(
            rf"\[({test_name})]\s+\[DTOR Call\s*\]\s+([\w:<>]+)::~([\w:<>]+)\((.*?)\)",
            line)
        #match_dtor_return = re.match()
        # CTOR
        if match_ctor_call:
            _, cls1, method, param = match_ctor_call.groups()
            # , inst, rtype, method_full, param, args
            #print(f'cls1: {cls1}, method: {method}, param: {param}')
            ctor_class = cls1
            ctor_text = f"{cls1}::{method}"

            # 생성 결과를 다음 CALL에서 추론
            # 생성자 이후의 CALL에서 등장하는 첫 번째 inst를 '생성된 객체'로 본다
            to_node = None
            for j in range(idx + 1, len(events)):
                m_call = re.match(
                    rf"\[{test_name}]\s+\[CALL\s*\] \((.*?)\)", events[j])
                if m_call:
                    to_node = m_call.group(1).strip()
                    break

            # 전역 함수일 경우 inst 이름 보정
            if to_node is None:
                to_node = f"{ctor_class}_UnknownInstance"

            if "::" not in ctor_text:
                inst_text = to_node
            else:
                inst_text = f"{ctor_class} @ {to_node}"

            # 노드가 없으면 추가
            if to_node not in node_keys:
                nodeDataArray.append({
                    "key": to_node,
                    "text": inst_text,
                    "isGroup": True,
                    "loc": compute_loc(inst_text, time_counter, position_state),
                    "duration": duration - 2
                })
                node_keys.add(to_node)


            # 생성자 호출자는 직전 CALL의 from
            # 생성자 호출자는 intent가 1 적은 CALL의 inst에서 찾기
            from_node = test_name
            ctor_target = None
            # for j in range(idx + 1, len(events)):
            #     m_call = re.match(rf"\[{test_name}]\s+\[CALL\s*\] \((.*?)\)", events[j])
            #     if m_call:
            #         ctor_target = m_call.group(1).strip()
            #         break

            if ctor_target:
                # intent가 1 작은 inst를 from_node로 추정
                for k in range(idx - 1, -1, -1):
                    m_prev_call = re.match(rf"\[{test_name}]\s+\[CALL\s*\] \((.*?)\)", events[k])
                    if m_prev_call:
                        caller_intent = m_prev_call.group(1).strip()
                        try:
                            # 주소 기반 비교 (정수로 해석 가능한 경우)
                            if int(caller_intent, 16) == int(ctor_target, 16) - 8:  # 보통 8바이트 기준
                                from_node = caller_intent
                                break
                        except ValueError:
                            pass  # 주소가 0 또는 정수가 아닐 수 있음


            linkDataArray.append({
                "from": from_node,
                "to": to_node,
                "text": "<<create>>",
                "time": time_counter
            })
            time_counter += 2

        # CALL
        elif match_call:
            _, inst, rtype, method_full, param, args = match_call.groups()
            inst = inst.strip()

            # 전역 함수 구분
            is_global_func = "::" not in method_full

            if is_global_func:
                method_name = method_full.strip()
                inst_key = f"{method_name}Instance"
                inst_text = inst_key
            else:
                method_base = method_full.split("::")[0]
                inst_key = inst
                inst_text = f"{method_base} @ {inst}"

            if inst_key not in node_keys:
                nodeDataArray.append({
                    "key": inst_key,
                    "text": inst_text,
                    "isGroup": True,
                    "loc": compute_loc(inst_text, None, position_state),
                    "duration": duration - 2
                })
                node_keys.add(inst_key)

            # from_node 계산
            from_node = test_name
            for prev in reversed(call_stack):
                if prev != inst_key:
                    from_node = prev
                    break

            call_text = f"{rtype.strip()} {method_full.strip()}({param.strip()})"
            if args:
                call_text += f" ({args.strip()})"

            linkDataArray.append({
                "from": from_node,
                "to": inst_key,
                "text": call_text,
                "time": time_counter
            })

            call_stack.append(inst_key)
            call_activation_map[inst_key] = time_counter
            time_counter += 2



        elif match_return:
            _, inst, rtype, method_full, param, retval = match_return.groups()
            inst = inst.strip()

            is_global_func = "::" not in method_full
            inst_key = f"{method_full.strip()}Instance" if is_global_func else inst

            from_node = inst_key
            to_node = test_name
            for i in range(len(linkDataArray) - 1, -1, -1):
                entry = linkDataArray[i]
                if entry["from"] == to_node:
                    to_node = entry["from"]
                    from_node = entry["to"]
                    break

            if inst_key in call_stack:
                call_stack.remove(inst_key)

            linkDataArray.append({
                "from": from_node,
                "to": to_node,
                "text": f"{retval.strip()} : {rtype.strip()}",
                "time": time_counter
            })
            time_counter += 2

            if inst_key in call_activation_map:
                start_time = call_activation_map[inst_key]
                duration_time = time_counter - start_time - 2
                activations.append({
                    "group": inst_key,
                    "start": start_time,
                    "duration": duration_time
                })
                del call_activation_map[inst_key]


        elif match_dtor_call:
            _, cls1, _, method = match_dtor_call.groups()

            from_node = None
            for i in range(len(linkDataArray) - 1, -1, -1):
                entry = linkDataArray[i]
                if entry["from"] == test_name and cls1 in entry["text"]:
                    candidate = entry["to"]
                    if candidate in node_keys and candidate not in destroyed_nodes:
                        from_node = candidate
                        destroyed_nodes.add(candidate)  # ✅ 한 번만 destroy
                        break

            if from_node:
                linkDataArray.append({
                    "from": from_node,
                    "to": test_name,
                    "text": "<<destroy>>",
                    "time": time_counter
                })
                time_counter += 2

    #print("here!")
    # 활성화 박스 노드 추가
    nodeDataArray.extend(activations)


    return {
        "class": "go.GraphLinksModel",
        "nodeDataArray": nodeDataArray,
        "linkDataArray": linkDataArray
    }

# ------------------------------
# 실행
# ------------------------------
# ------------------------------
# 실행 (여러 log 파일에서 테스트 단위로 분리하여 출력)
# ------------------------------
import os

def split_tests(lines):
    blocks = []
    current_block = []
    in_ctor_block = False
    in_run_block = False

    for i, line in enumerate(lines):
        # CTOR 기반 묶기
        if "[CTOR Call" in line:
            current_block = [line]
            in_ctor_block = True
            continue

        if in_ctor_block:
            current_block.append(line)
            if "[DTOR RETURN" in line:
                blocks.append(current_block)
                current_block = []
                in_ctor_block = False
            continue

        # Run-only 묶기
        if "Run 시작" in line and not in_run_block:
            current_block = [line]
            in_run_block = True
            continue

        if in_run_block:
            current_block.append(line)
            if "Run 끝" in line:
                blocks.append(current_block)
                current_block = []
                in_run_block = False
            continue

    return [b for b in blocks if len(b) > 1]



os.makedirs("output", exist_ok=True)

log_files = [f for f in os.listdir() if f.startswith("trace.log")]
for log_file in log_files:
    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    test_blocks = split_tests(lines)
    for block in test_blocks:
        for block in test_blocks:
            if len(block) < 2:
                continue  # 빈 블록 또는 한 줄만 있는 블록은 건너뜀

        # ✅ 테스트별 current_x 위치 초기화
        position_state["current_x"] = 360

        model = convert_to_gojs(block)
        test_name_match = re.match(r"\[([^\]]+)]", block[1])
    
        if test_name_match:
            test_name = test_name_match.group(1).replace("/", "_").replace(".", "_")
            filename = f"{os.path.splitext(log_file)[0]}_{test_name}.json"
            output_path = os.path.join("output", filename)
            with open(output_path, "w", encoding="utf-8") as out:
                json.dump(model, out, indent=2, ensure_ascii=False)

print("✅ 모든 테스트 JSON이 output 폴더에 생성되었습니다!")
