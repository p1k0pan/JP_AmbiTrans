# JP_AmbiTrans

## 目录
1. data 存放数据
2. API 存放api代码以及结果

## 日志
### 2025年5月12日
- [ ] 重跑qvq之前错误没有成功返回结果的部分，大概400条。cd到API目录下面，运行`python api_qvq_preview_miss.py --terminal 1`。生成结果在`/mnt/workspace/xintong/pjh/All_result/JP_AmbiTrans/qvq_preview推理翻译_v2重跑-{today}/`

### 2025年5月10日
- [x] cd到API目录下面，开启5个terminal，运行代码分别是 `python api_ambi_sense.py --terminal 1-5`。生成的结果在`/mnt/workspace/xintong/pjh/All_result/JP_AmbiTrans/gpt4o找歧义sense-{today}/`
- [x] cd到API目录下面，开启5个terminal，运行代码分别是 `python api_qvq_preview.py --terminal 1-5`。生成的结果在`/mnt/workspace/xintong/pjh/All\_result/JP_AmbiTrans/qvq_preview推理翻译_v2-{today}/`

### 2025年5月9日
- [x] 建立一个`/mnt/workspace/xintong/api_key.txt`, 第一行放API key，第二行放 base url
- [x] 在API目录下运行`api_qvq_preview.py`，开启5个terminal，运行代码分别是 `python api_qvq.py --terminal 1-5`。生成的结果在`result/qvq推理翻译{今天的日期}/`
