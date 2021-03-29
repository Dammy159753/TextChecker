#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time   : 2020/11/26 - 14:15
# @Modify : 2020/11/26 - 14:15
# @Author : dyu
# @File : testing.py
# @Function : 测试功能
import sys
sys.path.append("chinese_check")
sys.path.append("english_check")

import re, os, json, time
import requests
from check_controller import Controller
# from chinese_check.config import zh_check_config

from tqdm import tqdm

# query_json_en = {'grade':'junior', 'subject':'english', 'query':{"2973153279": {"question": "A naw repoot shows wwwhat life might be like in 100 years from now. www.  baidu.com It describes skyscrapers（摩天楼 that are much taller than today's buildings, underwater 'bubble' cities and holidays in space. The report is from a company. It asked experts（专家）on space and architecture（建筑）, as well as city planners, to give their ideas on the life in 2116. They said the way we live, work and play will be totally different to how we do these things today。 The experts used the Internet as an example. They said that 25 years ago, people could not imagine how the Internet and smartphones would change our lives. The Internet has completely changed the way we communicate, learn and do daily things. The experts said the changes in the next century would be even more unbelievable.Researchers questioned 2, 600 adults about the predictions（预言）they thought were most likely（很可能的）to happen in the future. They predicted that in the future, few people will go to an office but will work from home and have work meetings online. People will have highly developed 3-D printers that will let you download（下载）a design for furniture or a food recipe and then 'print' the sofa, table or pizza at home. Ｔhere will also be less need tor visits to the doctor. We will all have s home health instrument that will tell us what the problem is and give us treatment. We will also be going into space for holidays and to get resources that we have used up on Earth. A prediction that is missing is whether people will still need to study English.\t（1）The writer uses the example of the Internet in Paragraph 1 to show ______.\t（2）With the help of highly developed 3-D printers, a way to get a sofa in 2116 is to ______.\t（3）According to the passage, the missing prediction is ______.\t（4）The passage is mainly about ______.\t（5）The passage is most probably from ______.", "opts": [{"A": "the Internet was often used ", "B": "the Internet has developed fast", "C": "people will not believe the changes  ", "D": "technology will change people's lives"}, {"A": "buy one in a shop  ", "B": "ask somebody to make one", "C": "download a design and \"print\" one", "D": "design and make one by oneself"}, {"A": "how people will work", "B": "where people will get resources", "C": "what people will have at home to treat illness ", "D": "whether people will still need to learn English"}, {"A": "the life in 2116  ", "B": "holidays in space ", "C": "the history of the Internet ", "D": "medical treatment"}, {"A": "an advertisement   ", "B": "a newspaper ", "C": "a detective story ", "D": "a health report"}], "labels": ["科普知识类阅读", "说明文阅读", "细节理解题", "主旨大意题", "文章出处题"], "answers": ["A", "C", "D", "A", "B"], "solutions": ["（1）D 细节理解题。根据第一段中They said the way we live, work and play will be totally different to how we do these things today.他们说，我们的生活、工作和娱乐方式将与我们今天做这些事情的方式完全不同。可知，此处想利用互联网来表明：未来生活将因科技会发生很大变化。故选D。", "（2）C 细节理解题。根据第二段中People will have highly developed 3-D printers that will let you download（下载）a design for furniture or a food recipe and then 'print' the sofa, table or pizza at home.通过先进的3D打印机，人们可以下载家具设计以及美食菜谱，通过它们在家“打印”沙发、桌子或是披萨。故选C。", "（3）D 细节理解题。根据文章最后一句A prediction that is missing is whether people will still need to study English.可知人们不知道未来还需不需要学习英语。故选D。", "（4）A 主旨大意题。根据文章首句A new report shows what life might be like in 100 years from now...to give their ideas on the life in 2116.一份新的报告显示了100年后的生活可能会是什么样子…来表达他们对2116年生活的看法。可知这篇短文主要是关于2116年的生活。故选A。", "（5）B 文章出处题。根据短文大意可知，这是一篇预测未来生活的文章，最可能出现在报纸上。故选B。"], "explanations": ["", "", "", "", ""],  "type": "阅读理解"}}}
query_json_en = {"grade":"junior", "subject":"english", "query":{"_id":2973153279,"description":"What the relationship between Bill and Paul? A naw repoot shows wwwhat life might be like in 100 years from now. www.  baidu.com It describes skyscrapers（摩天楼 that are much taller than today's buildings, underwater 'bubble' cities and holidays in space. The report is from a company. www  .google.cnIt asked experts（专家on space and architecture（建筑）, as well as city planners, to give their ideas on the life in 2116. They said the way we live, work and play will be totally different to how we do these things today。 The experts used the Internet as an example. They said that 25 years ago，people could not imagine how the Internet and smartphones would change our lives. The Internet has completely changed the way we communicate, learn and do daily things。 The experts said the changes in the next century would be even more unbelievable.Researchers questioned 2, 600 adults about the predictions（预言）they thought were most likely（很可能的）to happen in the future. They predicted that in the future, few people will go to an office but will work from home and have work meetings online. People will have highly developed 3-D printers that will let you download（下载）a design for furniture or a food recipe and then 'print' the sofa, table or pizza at home. Ｔhere will also be ｌess need tor visits to the doctor. We will all have s home health instrument that will tell us what the problem is and give us treatment. We will also be going into space for holidays and to get resources that we have used up on Earth. A predction that is missing is whether people will still need to study English.","stems":[{"stem":"（1）The wrter uｓes the example of the Internet in Paragraph 1 to show ______.","option":{"A": "the Internet was often used ", "B": "the Internet has developed fast", "C": "people will not believe the changes  ", "D": "technology will change people's lives"}},{"stem":"（2）With the help of highly developed 3-D printers, a way to get a sofa in 2116 is to ______.","option":{"A": "buy one in a shop  ", "B": "ask somebody to make one", "C": "download a design and \"print\" one", "D": "design and make one by oneself"}},{"stem":"（3）According to the passage, the missing prediction is ______.","option":{"A": "how people will work", "B": "where people will get resources", "C": "what people will have at home to treat illness ", "D": "whether people will still need to learn English"}},{"stem":"（4）The passage is mainly about ______.","option":{"A": "the life in 2116  ", "B": "holidays in space ", "C": "the history of the Internet ", "D": "medical treatment"}},{"stem":"（5）The passage is most probably from ______.","option":{"A": "an advertisement   ", "B": "a newspaper ", "C": "a detective story ", "D": "a health report"}}],"labels":["科普知识类阅读", "说明文阅读", "细节理解题", "主旨大意题", "文章出处题"],"answers":["A", "C", "D", "A", "D"],"type":"阅读理解","solutions":["（1）D 细节理解（题。根据第一段中Ｔhey said the way we live, work and pｌay will be totally different to how we do these things today.他们说，我们的生活、工作和娱乐方式将与我们今天做这些事情的方式完全不同。可知，此处想利用互联网来表明：未来生活将因科技会发生很大变化。故选D。", "（2）C 细节理解题。根据第二段中Ｐeople will have highly developed 3-D printers that will let you download（下载）a design for furniture or a food recipe and then 'print' the sofa, table or pizza at home.通过先进的3D打印机，人们可以下载家具设计以及美食菜谱，通过它们在家“打印”沙发、桌子或是披萨。故选C。", "（3）D 细节理解题。根据文章最后一句A prediction that is missing is whether people will still need to study English.可知人们不知道未来还需不需要学习英语。故选D。", "（4）A 主旨大意题。根据文章首句A new report shows what life might be like in 100 years from now...to give their ideas on the life in 2116.一份新的报告显示了100年后的生活可能会是什么样子…来表达他们对2116年生活的看法。可知这篇短文主要是关于2116年的生活。故选A。", "（5）B 文章出处题。根据短文大意可知，这是一篇预测未来生活的文章，最可能出现在报纸上。故选B。"],"explanations":["", "", "", "", ""]}}

 
query_json_zh_1 = {'grade':'senior', 'subject':'history','query':{'3875322111':{"question": "李明班上来了一个新同学，他说：“我的姓是中国历史上的第一个王朝，大家猜猜我姓啥？”（        ）", "opts": [""], "labels": ["隋唐时期的书法和绘画艺术", "草书楷书和行书", "魏晋南北朝的绘画与石窟艺术"], "answers": [["兰亭序", "颜真卿"]], "solutions": ["约公元前2070年，禹建立我国历史上第一个王朝——夏朝，他的姓应该是夏。故选A。"], "explanations": ["本题考查夏朝的建立。"], "difficulty": 0.9, "type": "选择题"}}}

query_json_zh_2 = {'grade':'senior', 'subject':'history','query':{"3875322111":{"question": "李明班上来了一个新同学，他说：“我的姓是中国历史上的第一个王朝，大家猜猜我姓啥？”（        ）", "opts": [{"A": "夏", "B": "宋", "C": "唐", "D": "秦"}], "labels": ["夏朝的兴亡与“家天下”"], "answers": ["夏"], "solutions": ["约公元前2070年，禹建立我国历史上第一个王朝——夏朝，他的姓应该是夏。故选A。"], "explanations": ["本题考查夏朝的建立。"], "difficulty": 0.9, "type": "选择题"}}}

query_json_zh_3 = {'grade':'senior', 'subject':'history','query':{"1505932799":{ "question": "阅渎下列材斜，结合所學知识1199回答问题。材料一  农业社会里，生产力水平相对低下，。!与之相应的制度特点>是专制。但在前资本主义时期，中央集权制度不断加强和完善，这是中国制度建设的独特之处。……秦朝郡>县制的建立，是中央集权体制形式中最关键的步骤。中国古代“大一统”的政治格局的形成、发展，跟中央>集权制度的不断完善是密切相关的。——陶涛《关于“中央集权制”的几点思考》材料二  唐代制度，在下有……为政府公开选拔人才，在上有……综合管理全国行政事务。这两种制度，奠定了中国传统政治后一千年的稳固基础。——钱穆《国史新论》材料三  1644年4月25曰，明代崇祯皇帝自缢于北京禁苑煤山。1649年1月30>日，英国国王查理一世被送上了断头台。有学者把东西方这两位末代君主的暴亡，视为两个民族历史的一>个楔子——世界的天平开始失衡。\t（1）根据材料一，概括中国古代中央集权制度的特点。\t（2）材料二>中的“两种制度”分别指什么？为什么说“这两种制度，奠定了中国传统政治后一千年的稳固基础”？\t（3）如何理解材料三中“东西方这两位末代君主的暴亡，视为两个民族历史的一个楔子”？", "opts": ["", "", ""], "labels": ["东西方政治制度的比较", "英国君主立宪制", "中国古代政治制度的特点", "科举制", "隋唐三省六部制"], "answers": ["（1）特点：权力集中于中央（或皇帝总揽全国大权），中央对地方直接控制。", "（2）制度：科举制和三省六部制。原因：科举制把选拔人才和任命官吏的权力集中到中央政府，为历朝沿用，有利于中央集权的进一步加强。三省六部制削弱了相权，以保皇权独尊，此后历朝基>本沿用这种制度。", "（3）理解：西方的崛起和东方的没落加快；中国封建王朝进入末期，统治者不断加强君权专制统治，封建经济日益落后；英国进行资产阶级革命，确立资本主义君主立宪制度，有利于资本>主义发展。"], "solutions": ["（1）本题依据材       料一“与之相应的制度特点是专制”“秦朝郡县制的建立，是中央集权体制形式中最关键的步骤”可以得出，中国古代中央集权制度的特点是权力集中于中央，中央对地方直接控制。", "（2）第一小问依据材料二“唐代制度，在下有……为政府公开选拔人才，在上有……综合>管理全国行政事务”可知是指科举制、三省六部制。第二小问的原因，结合所学知识，从传统政治，即专制主义中央集权去理解两个制度的“作用”。", "（3）本题的理解结合清代统治者加强君主专制和英国君主立宪制确立的相关史实来回答，即西方的崛起和东方的没落加快；中国封建王朝进入末期，统治者不断加强>君权专制统治，封建经济日益落后；英国进行资产阶级革命，确立资本主义君主立宪制度，有利于资本主>义发展。"], "explanations": ["本题考查古代中国政治体制和英国君主立宪制，考查中国古代中央集权>制度的特点、科举制、三省六部制及其作用、中国古代君主专制制度与英国君主立宪制的影响。", "", ""], "difficulty": 0.1, "type": "材料分析题"}}}

query_json_zh_4 = {'grade':'senior', 'subject':'history','query':{"1515361279":{"question": "中学时代对人的一生有特别的意义，它见证着一个人由少年到        的生命进阶。（        ）", "opts": [{"A": "儿童", "B": "中年", "C": "青年", "D": "壮年"}], "labels": ["中学时代在生命历程中的重要作用"], "answers": ["C"], "solutions": ["成长中的每个阶段都有独特的价值和意义。中学时代是人生发展的一个新阶段。中学时代见证着一个人从少年到青年的生命进阶，Ｃ观点正确；Ａ、Ｂ、Ｄ观点错误。故选C。"], "explanations": [""], "difficulty": 0.1, "type": "选择题"}}}

query_json_zh_11 = {'subject':'history','query':["阅渎下列材斜，结合所學知识1199回答问题。材料一  农业社会里，生产力水平相对低下，。!与之相应的制度特点>是专制。但在前资本主义时期，中央集权制度不断加强和完善，这是中国制度建设的独特之处。……秦朝郡>县制的建立，是中央集权体制形式中最关键的步骤。中国古代“大一统”的政治格局的形成、发展，跟中央>集权制度的不断完善是密切相关的。——陶涛《关于“中央集权制”的几点思考》材料二  唐代制度，在下有……为政府公开选拔人才，在上有……综合管理全国行政事务。这两种制度，奠定了中国传统政治后一千年的稳固基础。——钱穆《国史新论》材料三  1644年4月25曰，明代崇祯皇帝自缢于北京禁苑煤山。1649年1月30>日，英国国王查理一世被送上了断头台。有学者把东西方这两位末代君主的暴亡，视为两个民族历史的一>个楔子——世界的天平开始失衡。\t（1）根据材料一，概括中国古代中央集权制度的特点。\t（2）材料二>中的“两种制度”分别指什么？为什么说“这两种制度，奠定了中国传统政治后一千年的稳固基础”？\t"]}


def simple_test(query):

    controller = Controller()
    check_result = controller.parse(query)
    # check_result = controller.parse_spellDetect(query)

    print(check_result)

    # print(zh_check_config['lac_segment']['word_loc'])
    # path = zh_check_config['lac_segment']['word_loc']


def batch_test():
    controller = Controller()

    n = 0
    error_list = []
    with open(r'/media/chen2/Text_Quality_Inspection/data/ques_data_20201111/高中生物_2020_1110.json', 'r', encoding='utf-8') as f:
        for line in tqdm(f.readlines()):
            dic = {}
            dic['grade'] = 'junior'
            dic['subject'] = 'politics'
            temp = {}
            temp_2 = {}
            line = eval(line.strip())
            temp['question'] = line['question']
            temp['opts'] = line['opts']
            temp['answers'] = line['answers']
            temp['solutions'] = line['solutions']
            temp['labels'] = line['labels']
            temp['type'] = line['type']
            temp['explanations'] = line['explanations']
            temp_2[str(line['_id'])] = temp
            dic['query'] = temp_2
            # for query in dic['query']:
            #     if query == '3847600383':
            #         print(dic)
            # print(dic)
            check_result = controller.parse(dic)
            if len(check_result) != 0:
                error_list.append(check_result)
                # print(line['_id'], check_result)
                n += 1
    print("一共有错误: ", n)
    print("----")
    return error_list


def api_test(query):
    # url = 'http://0.0.0.0:9559/text_quality_check'
    # url = 'http://172.18.1.117:9549/text_quality_check'
    # url = 'http://172.18.1.117:9549/tqc_spell_check'
    url = 'http://yj-ctb-tqc.haofenshu.com/text_quality_check'
    begin = time.time()

    r = requests.post(url, data=json.dumps(query))
    print(r.status_code)
    result_data = json.loads(r.text)
    print(result_data)
    print(time.time()-begin)
    

if __name__ == '__main__':
    # error_list = batch_test()
    # api_test(query_json_en)
    simple_test(query_json_en)
    # error_list = batch_test()
#
