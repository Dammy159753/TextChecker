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
import os
os.environ['CUDA_VISIBLE_DEVICES'] = "0"
from DatasetGenerate import calcTotal, saveData
import re, os, json, time
import requests
#from check_controller import Controller
# from chinese_check.config import zh_check_config

from tqdm import tqdm

# english testing datat
query_json_en = {"grade":"junior", "subject":"english", "query":
    {"_id":2973153279,
     "description":"What the relationship between Bill and Paul? A naw repoot shows wwwhat life might be like in 100 years from now. www.  baidu.com It describes skyscrapers（摩天楼 that are much taller than today's buildings, underwater 'bubble' cities and holidays in space. The report is from a company. www  .google.cnIt asked experts（专家on space and architecture（建筑）, as well as city planners, to give their ideas on the life in 2116. They said the way we live, work and play will be totally different to how we do these things today。 The experts used the Internet as an example. They said that 25 years ago，people could not imagine how the Internet and smartphones would change our lives. The Internet has completely changed the way we communicate, learn and do daily things。 The experts said the changes in the next century would be even more unbelievable.Researchers questioned 2, 600 adults about the predictions（预言）they thought were most likely（很可能的）to happen in the future. They predicted that in the future, few people will go to an office but will work from home and have work meetings online. People will have highly developed 3-D printers that will let you download（下载）a design for furniture or a food recipe and then 'print' the sofa, table or pizza at home. Ｔhere will also be ｌess need tor visits to the doctor. We will all have s home health instrument that will tell us what the problem is and give us treatment. We will also be going into space for holidays and to get resources that we have used up on Earth. A predction that is missing is whether people will still need to study English.",
     "stems":[{"stem":"（1）The wrter uｓes the example of the Internet in Paragraph 1 to show ______.",
               "option":{"A": "the Internet was often used ", "B": "the Internet has developed fast", "C": "people will not believe the changes  ", "D": "technology will change people's lives"}},
              {"stem":"（2）With the help of highly developed 3-D printers, a way to get a sofa in 2116 is to ______.",
               "option":{"A": "buy one in a shop  ", "B": "ask somebody to make one", "C": "download a design and \"print\" one", "D": "design and make one by oneself"}},
              {"stem":"（3）According to the passage, the missing prediction is ______.",
               "option":{"A": "how people will work", "B": "where people will get resources", "C": "what people will have at home to treat illness ", "D": "whether people will still need to learn English"}},
              {"stem":"（4）The passage is mainly about ______.",
               "option":{"A": "the life in 2116  ", "B": "holidays in space ", "C": "the history of the Internet ", "D": "medical treatment"}},
              {"stem":"（5）The passage is most probably from ______.",
               "option":{"A": "an advertisement   ", "B": "a newspaper ", "C": "a detective story ", "D": "a health report"}}],
     "labels":["科普知识类阅读", "说明文阅读", "细节理解题", "主旨大意题", "文章出处题"],
     "answers":["A", "C", "D", "A", "D"],
     "type":"阅读理解",
     "solutions":["（1）D 细节理解（题。根据第一段中Ｔhey said the way we live, work and pｌay will be totally different to how we do these things today.他们说，我们的生活、工作和娱乐方式将与我们今天做这些事情的方式完全不同。可知，此处想利用互联网来表明：未来生活将因科技会发生很大变化。故选D。", "（2）C 细节理解题。根据第二段中Ｐeople will have highly developed 3-D printers that will let you download（下载）a design for furniture or a food recipe and then 'print' the sofa, table or pizza at home.通过先进的3D打印机，人们可以下载家具设计以及美食菜谱，通过它们在家“打印”沙发、桌子或是披萨。故选C。", "（3）D 细节理解题。根据文章最后一句A prediction that is missing is whether people will still need to study English.可知人们不知道未来还需不需要学习英语。故选D。", "（4）A 主旨大意题。根据文章首句A new report shows what life might be like in 100 years from now...to give their ideas on the life in 2116.一份新的报告显示了100年后的生活可能会是什么样子…来表达他们对2116年生活的看法。可知这篇短文主要是关于2116年的生活。故选A。", "（5）B 文章出处题。根据短文大意可知，这是一篇预测未来生活的文章，最可能出现在报纸上。故选B。"],
     "explanations":["", "", "", "", ""]}}

# 错词功能新接口
query_json_spell_1 = {'subject': 'history', 'query':
    ["阅渎下列材斜，结合所學知识1199回答问题。材料一  农业社会里，生产力水评相对低下，与之相应的制度特点>是专制。但在前资本主义时期，中央集汉制度不断加强和完善，这是中国制度建没的独特之处。……秦朝郡>县制的建立，是中央集权体制形式中最关键的步骤。中国古代“大一统”的政治格局的形成、发展，跟中央>集权制度的不断完善是密切相关的。——陶涛《关于“中央集权制”的几点思考》材料二  唐代制度，在下有……为政府公开选拔人才，在上有……综合管理全国行政事务。这两种制度，奠定了中国传统政治后一千年的稳固基础。——钱穆《国史新论》材料三  1644年4月25曰，明代崇祯皇帝自缢于北京禁苑煤山。1649年1月30>日，英国国王查理一世被送上了断头台。有学者把东西方这两位末代君主的暴亡，视为两个民族历史的一>个楔子——世界的天平开始失衡。\t（1）根据材料一，概括中国古代中央集权制度的特点。\t（2）材料二>中的“两种制度”分别指什么？为什么说“这两种制度，奠定了中国传统政治后一千年的稳固基础”？\t"]}

query_json_spell_2 = {'subject':'history', 'query':
                      ['2019—2020学年第二学期期末评估试卷 6．澶渊之盟后，宋辽边境“生育蕃息，牛羊被野（遍地），戴白之人，不识干戈（战争）” 这说明澶渊之盟 七年级历史 A．维持了宋辽间的长久和平 B．实现宋辽双方的完全平等 C．直接导致南方经济的繁柴 D．使北宋军事力量完全瓦解 叩 注意事项： 7．有一位历史人物与“精忠报国”“还我河山”“郾城大捷”有关，此人是 1、本试卷共6页，分为选择题和非选择题，满分50分. 2、开卷考试，可查阅资料，但应独立答题，禁止交流资料。 A．文天祥 B．岳飞 C．郑成功 D．渥巴锡 3、本试卷上不要答题，请按答题卡上注意事项的要求直接把答案填写在答题卡上。答在 8．《元史》评价成吉思汗“帝深沉有大略，用兵如神，故能灭国四十，遂平西夏。其奇勋 试卷上的答案无效。 伟迹甚众，惜乎当时史官不备，或多失于纪载云。”成吉思汗的主要事迹是 体 掷 第一部分选择题（共20小题，20分） A．统一蒙古各部 B．联宋灭金 米 下列每小题列出的四个选项中，只有一项是最符合题目要求的。请将正确选项的英文字母 C．建立元朝 D．灭南宋统一企国 代号涂写在答题卡相应位置上。 9．司马光和司马迁，被后人称为“史学两司马”。北宋著名史学家司马光主持编写的，并 1．下列哪一史实结束了长期分裂的局面，顺应了我国统一多民族国家的历史发展大趋势 由宋神宗以“鉴于往事，有资于治道”赐名的史学巨著是 A．隋文帝灭掉陈朝 B．隋朝创立科举制 A．《战国策》 B．《新五代史》 C．《史记》 D．《资治通鉴》 C．隋朝统一度量衡 D．隋朝开通大运河 10．《明史•宋濂传》记述：大学士宋濂上朝，朱元璋问他昨天在家请客没有，客人是谁， 国 $ 2．历史叙述有历史陈述、历史评价等方式。其中，历史评价是指对历史现象和历史事实 吃的什么菜，宋濂一一照实回答，朱元璋很满意说：“你没有欺骗我。”这一记载可以用于研究 进行态度与价值的评判表述。下列选项属于历史评价的是 A．朱元璋提倡尊孔崇儒 B．明初大大强化皇权 都 A．汉武帝在长安兴办太学，大力推行儒学教育 C．明朝的君臣关系和睦 D．明初朝臣权力过大 B．“贞观之治”和“开元盛世”都是中国古代治世 11．明朝时期著名的丝织业中心和制瓷中心分别是 C．由越南传入的占城稻成熟早，抗旱力强，北宋时推广至东南地区 A．海南岛、定窑 B．开封、汝瓷 C．苏州、景德镇 D．南京、哥窑 救 D．清朝雍正皇帝设置了军机处 12．2020年春，一场突如其来的新型冠状病毒从武汉迅速向全国蔓延。在疫情防治中，中 3．2020年初国内新冠肺炎疫悄发生后，引起了世界各国人民的关注。日本迅速募集物资 医药发挥了很大作用。下列可以给我们提供医疗和防治帮助的中医著作是 驰援，日本汉语水平考试HSK事务捐赠的驰援物资包装箱上用中文写有“山川异域，日月同天”， A．《天工开物》 B．《农政全书》 C．《齐民要术》 D．《本草纲目》 寄托了日本人民的深情厚谊。在唐代，也有一段中日友好交往的佳话，它是 13．李自成领导的农民起义军提出“均田免赋”的口号，受到广大农民的热烈欢迎。其根本 抑 A．张骞出使西域 B．文成公主入藏 原因是 补 C．鉴真东渡 D．玄奘西行 A．倭寇猖獗，外患严重 B．农民觉悟高，拥护起义军 4．唐朝从“小邑犹藏万家室”到“人烟断绝，千里萧条”的转折点是 C．经济发展，出现商帮 D．明末政治腐败，赋税沉重 A．开凿运河 B．安史之乱 C．黄巢起义 D．靖康之变 14．“从戚继光抗倭到郑成功收复台湾再到雅克萨之战，从册封达赖、班禅到设置驻藏大 5．多数谚语反映了当时人民的生活实践经验。宋初有谚语曰：“做人莫做军，做铁莫做针。” 臣再到设置伊犁将年”。如果给上述史实提炼一个主题，较为合理的是 这说明当时社会 A．国家的巩固与发展 B．文化的碰撞与交流 u A．重武轻文 B．重视科学 C．重文轻武 D．重视商业 C．外交的开放与危机 D．经济的繁荣与稳定 七年级历史第1页（共6页） 七年级历史第2页（共6页）']}
# 符号混用方法检验； 空格过多校验；错词功能那个检验；繁简字检验；
query_json_zh_1 = {'grade': 'senior', 'subject': 'history', 'query': {
    "_id":1505932799,
    "description": "阅渎下列材斜，结合所學知识1199回答问题。材料一  农业社会里，生产力水平相对低下，。!与之相应的制度特点是馬上专制。但在前资本主义时期，中央集权制度不断加强和完善，这是中国制度建设的独特之处。……秦朝郡>县制的建立，是中央集权体制形式中最关键的步骤。中国古代“大一统”的政治格局的形成、发展，跟中央>集权制度的不断完善是密切相关的。——陶涛《关于“中央集权制”的几点思考》材料二  唐代制度，在下有……为政府公开选拔人才，在上有……综合管理全国行政事务。这两种制度，奠定了中国传统政治后一千年的稳固基础。——钱穆《国史新论》材料三  1644年4月25曰，明代崇祯皇帝自缢于北京禁苑煤山。1649年1月30>日，英国国王查理一世被送上了断头台。有学者把东西方这两位末代君主的暴亡，视为两个民族历史的一>个楔子——世界的天平开始失衡。",
    "stems": [{'stem':"（1）根据材料一，概括中国古代中央集汉制度的特点。"},
              {'stem':"（2）材料二>中的“两种制度”分别指什么？为什么说“這两种制度，奠定了中国传统政治后一千年的稳固基础”？"},
              {'stem':'（3）如何理解材料三中“东西方这两位末代君主的暴亡，视为两个民族历史的一个楔子”？'}],
    "labels": ["东西方政治制度的比较", "英国君主立宪制", "中国古代政治制度的特点", "科举制", "隋唐三省六部制"],
    "answers": ["（1）特点：权力集中于中央（或皇帝总揽全国大权），中央对地方直接控制。",
                "（2）制度：科举制和三省六部制。原因：科举制把选拔人才和任命官吏的权力集中到中央政府，为历朝沿用，有利于中央集权的进一步加强。三省六部制削弱了相权，以保皇权独尊，此后历朝基>本沿用这种制度。",
                "（3）理解：西方的崛起和东方的没落加快；中国封建王朝进入末期，统治者不断加强君权专制统治，封建经济日益落后；英国进行资产阶级革命，确立资本主义君主立宪制度，有利于资本>主义发展。"],
    "solutions": ["（1）本题依据材       料一“与之相应的制度特点是专制”“秦朝郡县制的建立，是中央集权体制形式中最关键的步骤”可以得出，中国古代中央集权制度的特点是权力集中于中央，中央对地方直接控制。",
                  "（2）第一小问依据材料二“唐代制度，在下有……为政府公开选拔人才，在上有……综合>管理全国行政事务”可知是指科举制、三省六部制。第二小问的原因，结合所学知识，从传统政治，即专制主义中央集权去理解两个制度的“作用”。",
                  "（3）本题的理解结合清代统治者加强君主专制和英国君主立宪制确立的相关史实来回答，即西方的崛起和东方的没落加快；中国封建王朝进入末期，统治者不断加强>君权专制统治，封建经济日益落后；英国进行资产阶级革命，确立资本主义君主立宪制度，有利于资本主>义发展。"],
    "explanations": ["本题考查古代中国政治体制和英国君主立宪制，考查中国古代中央集权>制度的特点、科举制、三省六部制及其作用、中国古代君主专制制度与英国君主立宪制的影响。", "", ""],
    "difficulty": 0.1,
    "type": "材料分析题"}}

def simple_test(query):

    controller = Controller()
    check_result = controller.parse(query)
    # check_result = controller.parse_spellDetect(query)

    print(check_result)
    return check_result

def batch_test():
    controller = Controller()

    n = 0
    error_list = []
    # ques_data_2021_0222
    with open(r'/media/chen2/Text_Quality_Inspection/data/ques_data_2021_0222/高中物理_2021_0222.json', 'r', encoding='utf-8') as f:
        for line in tqdm(f.readlines()):
            dic = {}
            dic['grade'] = 'junior'
            dic['subject'] = 'physics'
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
   # url = 'http://172.18.1.117:9660/text_quality_check'
    url = 'http://172.18.1.117:9770/tqc_spell_check'
    # url = 'http://yj-ctb-tqc.haofenshu.com/text_quality_check'
    begin = time.time()

    r = requests.post(url, data=json.dumps(query))
    print(r.status_code)
    result_data = json.loads(r.text)
    print(result_data)
    print(time.time()-begin)
    



if __name__ == '__main__':
    # error_list = batch_test()
    # _list = calcTotal(error_list)
    # saveData(error_list, _list, '初中物理')

    # simple_test(query_json_en)
    error_list = simple_test(query_json_zh_1)
    # api_test(query_json_spell_1)

    # error_list = batch_test()
#
