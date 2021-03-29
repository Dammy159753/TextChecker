# 切分数据集

data_file = r"/media/chen2/fxj/Text_Quality_Check_dev/english_check/test/test_data/writing_and_reading.json"
with open(data_file,'r',encoding='utf-8') as rf:
    lines = rf.readlines()
    res_num = len(lines)
    batch_size = 1000
    batch_num = 0
    while res_num > 0:
        save_file = r"/media/chen2/fxj/Text_Quality_Check_dev/english_check/test/test_data/batch_{}.json".format(batch_num+1)
        start_index = batch_num * batch_size
        with open(save_file,'a',encoding='utf-8') as af:
            for line in lines[start_index:start_index + batch_size - 1]:
                af.write(line)
        res_num -= batch_size
        batch_num += 1
            
