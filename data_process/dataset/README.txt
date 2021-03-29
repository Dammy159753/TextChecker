一、训练/测试 数据格式说明：
1.1 包含4个文件，其中两个数据文件，一个sim_question_train.txt，一个sim_question_test.txt；另外有还有两个文件是题目id的对应关系，分别是relation_train.txt和relation_test.txt.
1.2 题目数据文件中中的每一行是一个样例，每一个样例由一对题干pair以及相应的相关性标注组成，分三列，用'@@@@@'分隔，第一列和第二列为题目1和题目2，第三列为相关性标注，1表示这两个题目相关，0表示不相关。
1.3 relation_train.txt和sim_question_train.txt对应，这两个文件的每一行数据是一一对应的，前者是题目id的对应和标注，后者是具体题干文本及其对应的题干文本和相关性标注，每一道题对应多个其他题。


二、数据处理功能类.py说明
toolbox.py                   Variety Tools Box 1.源数据中重复和近似相近的数据 2.分词方法 
make_dataset.py              制作数据集和预处理的一些功能方法 
math_cleaner.py              补充原始答案信息，并且处理公式以及清洗过程
fill_answer.py               填充答案的功能类 （由math_cleaner.py 调用）


三、数据文件说明
3.1  整体数据（高中数学）

(1) 高中数学全量.json              数学数据原始数据（全量）

(2) all_math_data_origin.json      高中数学原始未填充答案数据

(3) all_math_data_newest.json      高中数学原始填充答案后数据

(4) senior_math_all_field_info_data.json 高中全量数据所有字段信息

(5) doc_mapping.json               序号与tid的映射表

(6) all_tid_sample_pair.json       高中数学所有tid的样本对

(7) elite_subject.json             高中数学精品题库

(8) gaozhong_math_info.json        高中数学原题-相似题关系全部字段信息（也是对应关系表）

(9) except_tid.txt                 异常tid数据记录


3.2  向量模型数据
(1) scaler_math_new_57w        数学标量向量模型
(2) word2vec_math_new_57w      数学科目的词向量模型

(3) vector.npy                 深度语义向量储存文件
(4) stopword.txt               停用词表

(5) math_words.txt             数学词表（TXT格式）
(6) math_w2idic.json           数学词表（JSON格式）

3.3  其他数据
./data下：
elite_index.txt            精品题tid

ori2sim_map.json           原题-相似题映射关系

3.4 doc2vec模型数据
./doc2vec下

3.5 训练数据
./train_data下

3.6 测试数据  
./test_data下

3.7 预测数据
./predict_data下






































