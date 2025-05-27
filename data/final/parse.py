import json

import re
import sys


def clean_json_string(s):
    # 如果有```json ... ```包住的
    match = re.search(r'```json\s*(.*?)\s*```', s, re.DOTALL)
    if match:
        s = match.group(1)
        s = re.sub(r',?\s*\.\.\.', '', s)
        s = re.sub(r'(?<!:)//.*', '', s)

        return s

    s = re.sub(r'(?<!:)//.*', '', s)
    s = re.sub(r',?\s*\.\.\.', '', s)



    # 否则自己手动匹配大括号
    start = s.find('{')
    if start == -1:
        return s  # fallback, 没有JSON

    count = 0
    for i in range(start, len(s)):
        if s[i] == '{':
            count += 1
        elif s[i] == '}':
            count -= 1
            if count == 0:
                # 找到完整JSON
                return s[start:i+1]

    return s  # fallback


def extract_ambiguities(json_string):
    cleaned = clean_json_string(json_string)

    # 加上错误处理，避免非标准 json 直接崩掉
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        print("⚠️ 解析失败，跳过这一条。内容是：", cleaned)
        # sys.exit()
        return None

    return data



if __name__ == "__main__":
    data = json.load(open("/Users/piko/Desktop/JP_AmbiTrans/data/final/qwen-max-latest_ambi_normal_test.json", "r", encoding="utf-8"))
    # limit = [0, 303, 550, 623, 749, 789, 813, 853, 862, 888, 945, 1213, 1278, 1516, 1615, 1675, 1817]
    for item in data:
        # if item["idx"] != 39:
        #     continue
        ambi = item["bad_sense"]
        res = extract_ambiguities(ambi)
        item["bad_sense"] = res
    json.dump(data, open("ambi_normal_test_bad_sense.json", "w", encoding="utf-8"), ensure_ascii=False, indent=4)

    # data = json.load(open("qwen-max_ovl_result_parsed.json", "r", encoding="utf-8"))
    # t = []
    # for item in data:
    #     if item["result"]["has_two_level_ambiguity"] == True:
    #         t.append(item)
    # print("两阶段歧义的数量：", len(t))
    # json.dump(t, open("qwen-max_ovl_result_parsed_two_level.json", "w", encoding="utf-8"), ensure_ascii=False, indent=4)

    # data = json.load(open("gpt4o_ambi.json", "r", encoding="utf-8"))
    # print("数据集大小：", len(data))
    # en = 0
    # zh = 0
    # for item in data:
    #     score_res = item["score_result"]
    #     if score_res is None:
    #         continue
    #     ambiguous_in_en = score_res.get("ambiguous_in_en", False)
    #     zh_resolves_ambiguity = score_res.get("zh_resolves_ambiguity", False)
    #     if ambiguous_in_en:
    #         en += 1
    #     if zh_resolves_ambiguity:
    #         zh += 1
    #     if not ambiguous_in_en and zh_resolves_ambiguity:
    #         print("⚠️ 发现英文句子没有歧义，但中文翻译解决了歧义。", item["idx"])
    # print("英文句子有歧义的数量：", en)
    # print("中文翻译解决歧义的数量：", zh)


    
