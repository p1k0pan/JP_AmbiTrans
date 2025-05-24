import json
from re import split


data = json.load(open('/Users/piko/Desktop/JP_AmbiTrans/data/图文匹配/train_plus_图文匹配.json'))

# Split data into 10 parts
split_size = len(data) // 5
split_data = [data[i*split_size:(i+1)*split_size] for i in range(5)]

# Save each part into separate files
i = 0
for part in split_data:
    print(len(part))
    with open(f"train_plus_图文匹配_part{i+1}.json", 'w', encoding='utf-8') as f:
        json.dump(part, f, indent=4, ensure_ascii=False)
    i += 1


# all = []
# idx = 0
# total = 0
# for i in range(1,11):
#     data=json.load(open(f'qwen-max-2025-01-25_hyper_train_plus_图文匹配_part_{i}.json'))
#     total += len(data)
#     for item in data:
#         item["idx"] = idx
#         idx += 1
#         all.append(item)
#     print("total", total)

# print(total)
# json.dump(all, open("qwen-max-2025-01-25_hyper_train_plus_图文匹配.json", "w"), ensure_ascii=False, indent=4)

