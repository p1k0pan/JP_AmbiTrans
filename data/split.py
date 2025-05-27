import json
from re import split


# data = json.load(open('/Users/piko/Desktop/JP_AmbiTrans/data/final/ambi_normal_test.json'))

# # Split data into 10 parts
# split_size = len(data) // 3
# split_data = [data[i*split_size:(i+1)*split_size] for i in range(3)]

# # Save each part into separate files
# i = 0
# for part in split_data:
#     print(len(part))
#     with open(f"/Users/piko/Desktop/JP_AmbiTrans/data/final/ambi_normal_test_part_{i+1}.json", 'w', encoding='utf-8') as f:
#         json.dump(part, f, indent=4, ensure_ascii=False)
#     i += 1


all = []
idx = 0
total = 0
for i in range(1,4):
    data=json.load(open(f'/Users/piko/Desktop/JP_AmbiTrans/data/final/qwen-max-latest_ambi_normal_test_part_{i}.json'))
    total += len(data)
    for item in data:
        item["idx"] = idx
        idx += 1
        all.append(item)
    print("total", total)

print(total)
json.dump(all, open("/Users/piko/Desktop/JP_AmbiTrans/data/final/qwen-max-latest_ambi_normal_test.json", "w"), ensure_ascii=False, indent=4)

