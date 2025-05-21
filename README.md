# JP_AmbiTrans

## 目录
1. data 存放数据
2. API 存放api代码以及结果

## 日志
### 2025年5月21日
- cd到API目录下，找具体翻译词。运行代码是`python api_qwenvl_specific_words.py`。生成结果在`/mnt/workspace/xintong/pjh/All_result/JP_AmbiTrans/qwenvl_找具体词-{today}/`
- cd到API目录下，找二级歧义词。运行代码是`python api_qwen_two_level.py`。生成结果在`/mnt/workspace/xintong/pjh/All_result/JP_AmbiTrans/qwenvl_找具体词-{today}/`

### 2025年5月13日
- [x] cd到API目录下，只用一个terminal跑一部分数据验证`qvq-max`的推理链路。运行代码是`python api_qvq-max.py --terminal 1`。生成结果在`/mnt/workspace/xintong/pjh/All_result/JP_AmbiTrans/qvq-max消歧链路-{today}/`
- [x] cd到API目录下，只用一个terminal跑一部分数据验证`o1`或者`o3`（**目前代码写的是o1模型名称，如果有o3要手动写入正确的模型名称**）的推理链路。运行代码是`python api_o13.py --terminal 1`。生成结果在`/mnt/workspace/xintong/pjh/All_result/JP_AmbiTrans/{model_name}消歧链路-{today}/`

### 2025年5月10日
- [x] cd到API目录下面，开启5个terminal，运行代码分别是 `python api_ambi_sense.py --terminal 1-5`。生成的结果在`/mnt/workspace/xintong/pjh/All_result/JP_AmbiTrans/gpt4o找歧义sense-{today}/`
- [x] cd到API目录下面，开启5个terminal，运行代码分别是 `python api_qvq_preview.py --terminal 1-5`。生成的结果在`/mnt/workspace/xintong/pjh/All\_result/JP_AmbiTrans/qvq_preview推理翻译_v2-{today}/`

### 2025年5月9日
- [x] 建立一个`/mnt/workspace/xintong/api_key.txt`, 第一行放API key，第二行放 base url
- [x] 在API目录下运行`api_qvq_preview.py`，开启5个terminal，运行代码分别是 `python api_qvq.py --terminal 1-5`。生成的结果在`result/qvq推理翻译{今天的日期}/`
