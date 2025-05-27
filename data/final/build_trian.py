import json
import copy

mma = json.load(open('/Users/piko/Desktop/JP_AmbiTrans/data/final/mma_test.json'))
sp = json.load(open('/Users/piko/Desktop/JP_AmbiTrans/data/final/sp_test_bad.json'))

# for i in range(len(mma)):
#     item = mma[i]
#     sense = item["sense"][0]
#     if i %2 ==0:
#         bad_sense = copy.deepcopy(mma[i+1]['sense'][0])
#         bad_sense["bad_interpretation"] = bad_sense.pop("gold_interpretation")
#     else:
#         bad_sense = copy.deepcopy(mma[i-1]['sense'][0])
#         bad_sense["bad_interpretation"] = bad_sense.pop("gold_interpretation")
#     item["bad_sense"] = [bad_sense]
# json.dump(mma, open('/Users/piko/Desktop/JP_AmbiTrans/data/final/mma_test_bad.json', 'w'), ensure_ascii=False, indent=4)


for item in sp:
    sense = item["sense"]
    bad_sense = item["bad_sense"]

    assert len(sense) == len(bad_sense), "Sense and bad sense lists must be of the same length"

    new_bad = []
    for s, b in zip(sense, bad_sense):
        assert s["term"] == b["term"], "Terms in sense and bad sense must match"
        if s["gold_interpretation"] != b["bad_interpretation"]:
            new_bad.append(b)
        item["bad_sense"] = new_bad
json.dump(sp, open('/Users/piko/Desktop/JP_AmbiTrans/data/final/sp_test_bad2.json', 'w'), ensure_ascii=False, indent=4)
    

