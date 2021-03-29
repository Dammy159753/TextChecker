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

from tqdm import tqdm
query_json_en = {"grade":"junior", "subject":"english", "query":{"_id":2973153279,"description":"What the relationship between Bill and Paul? A naw repoot shows wwwhat life might be like in 100 years from now. www.  baidu.com It describes skyscrapers（摩天楼 that are much taller than today's buildings, underwater 'bubble' cities and holidays in space. The report is from a company. www  .google.cnIt asked experts（专家on space and architecture（建筑）, as well as city planners, to give their ideas on the life in 2116. They said the way we live, work and play will be totally different to how we do these things today。 The experts used the Internet as an example. They said that 25 years ago，people could not imagine how the Internet and smartphones would change our lives. The Internet has completely changed the way we communicate, learn and do daily things。 The experts said the changes in the next century would be even more unbelievable.Researchers questioned 2, 600 adults about the predictions（预言）they thought were most likely（很可能的）to happen in the future. They predicted that in the future, few people will go to an office but will work from home and have work meetings online. People will have highly developed 3-D printers that will let you download（下载）a design for furniture or a food recipe and then 'print' the sofa, table or pizza at home. Ｔhere will also be ｌess need tor visits to the doctor. We will all have s home health instrument that will tell us what the problem is and give us treatment. We will also be going into space for holidays and to get resources that we have used up on Earth. A predction that is missing is whether people will still need to study English.","stems":[{"stem":"（1）The wrter uｓes the example of the Internet in Paragraph 1 to show ______.","option":{"A": "the Internet was often used ", "B": "the Internet has developed fast", "C": "people will not believe the changes  ", "D": "technology will change people's lives"}},{"stem":"（2）With the help of highly developed 3-D printers, a way to get a sofa in 2116 is to ______.","option":{"A": "buy one in a shop  ", "B": "ask somebody to make one", "C": "download a design and \"print\" one", "D": "design and make one by oneself"}},{"stem":"（3）According to the passage, the missing prediction is ______.","option":{"A": "how people will work", "B": "where people will get resources", "C": "what people will have at home to treat illness ", "D": "whether people will still need to learn English"}},{"stem":"（4）The passage is mainly about ______.","option":{"A": "the life in 2116  ", "B": "holidays in space ", "C": "the history of the Internet ", "D": "medical treatment"}},{"stem":"（5）The passage is most probably from ______.","option":{"A": "an advertisement   ", "B": "a newspaper ", "C": "a detective story ", "D": "a health report"}}],"labels":["科普知识类阅读", "说明文阅读", "细节理解题", "主旨大意题", "文章出处题"],"answers":["A", "C", "D", "A", "D"],"type":"阅读理解","solutions":["（1）D 细节理解（题。根据第一段中Ｔhey said the way we live, work and pｌay will be totally different to how we do these things today.他们说，我们的生活、工作和娱乐方式将与我们今天做这些事情的方式完全不同。可知，此处想利用互联网来表明：未来生活将因科技会发生很大变化。故选D。", "（2）C 细节理解题。根据第二段中Ｐeople will have highly developed 3-D printers that will let you download（下载）a design for furniture or a food recipe and then 'print' the sofa, table or pizza at home.通过先进的3D打印机，人们可以下载家具设计以及美食菜谱，通过它们在家“打印”沙发、桌子或是披萨。故选C。", "（3）D 细节理解题。根据文章最后一句A prediction that is missing is whether people will still need to study English.可知人们不知道未来还需不需要学习英语。故选D。", "（4）A 主旨大意题。根据文章首句A new report shows what life might be like in 100 years from now...to give their ideas on the life in 2116.一份新的报告显示了100年后的生活可能会是什么样子…来表达他们对2116年生活的看法。可知这篇短文主要是关于2116年的生活。故选A。", "（5）B 文章出处题。根据短文大意可知，这是一篇预测未来生活的文章，最可能出现在报纸上。故选B。"],"explanations":["", "", "", "", ""]}}
# 错词功能新接口
query_json_spell_1 = {'subject': 'history', 'query':
    ["阅渎下列材斜，结合所學知识1199回答问题。材料一  农业社会里，生产力水评相对低下，与之相应的制度特点>是专制。但在前资本主义时期，中央集汉制度不断加强和完善，这是中国制度建没的独特之处。……秦朝郡>县制的建立，是中央集权体制形式中最关键的步骤。中国古代“大一统”的政治格局的形成、发展，跟中央>集权制度的不断完善是密切相关的。——陶涛《关于“中央集权制”的几点思考》材料二  唐代制度，在下有……为政府公开选拔人才，在上有……综合管理全国行政事务。这两种制度，奠定了中国传统政治后一千年的稳固基础。——钱穆《国史新论》材料三  1644年4月25曰，明代崇祯皇帝自缢于北京禁苑煤山。1649年1月30>日，英国国王查理一世被送上了断头台。有学者把东西方这两位末代君主的暴亡，视为两个民族历史的一>个楔子——世界的天平开始失衡。\t（1）根据材料一，概括中国古代中央集权制度的特点。\t（2）材料二>中的“两种制度”分别指什么？为什么说“这两种制度，奠定了中国传统政治后一千年的稳固基础”？\t"]}

query_json_spell_2 = {'subject':'history','query':
                      ['2019-2020学年度第二学期期末质量检测 13．中华民族现在由56个民族组成，在历史上有一个新的民族叫回回民族形成于（        ） A．唐朝 B．元朝 C．明朝 D．清朝 七年级历史试卷 14．宋朝时期，由于市民阶层不断壮大，在城市中出现的休闲娱乐场所是（        ） 一、单选题（本大题共20小题，共50分） A．市 B．坊 C．勾栏 D．瓦子 1．隋朝时开凿的大运河是世界上的伟大工程之一，这条运河的中心是（        ） 15．“靖康耻，犹未雪；臣子恨，何时灭。驾长车，踏破贺兰山缺。壮志饥餐胡虏肉，笑谈渴饮匈奴血。 A．长安 B．涿郡 C．洛阳 D．余杭 待从头，收拾旧山河，朝天阙！”其中“靖康耻”发生于（        ） 2．“忆昔开元全盛日，小邑犹藏万家室。稻米流脂粟米白，公私仓廪俱丰实。”诗中描绘的是哪位皇帝 A.1115年 B.1126年 C.1127年 D.1140年 统治时期的景象（        ） 16．明太祖朱元璋废除丞相的主要目的是（        ） A．隋文帝 B．唐太宗 C．武则天 D．唐玄宗 A．强化君主专制 B．提高办事效率 3．唐朝的富强，促进了文化艺术的繁荣，在唐朝文学里，最光彩夺目的，成就最高的是（        ） C．让“群臣”监督皇帝 D．精简政府机构 A．辞赋 B．诗歌 C．散文 D．词曲 17．澳门自1999年回归后，成为中华人民共和国的一个特别行政区。1553年，攫取在我国澳门居住权的殖 4．唐朝时既是一座国际性的大都市，也是当时各民族交往的中心，这座城市是（        ） 民者是（        ） A．洛阳 B．长安 C．扬州 D．成都 A．西班牙 B．日本 C．荷兰 D．葡萄牙 6．唐朝曾经是一个强盛的朝代，有盛就会衰，导致唐朝由盛转衰的事件是（        ） 18．下列对文字狱的解释，最准确的是（        ） A．安史之乱 B．藩镇割据 C．黄巢起义 D．宦官专权 A．迫害知识分子的冤狱 B．关押知识分子的监狱 6．唐朝灭亡后，全国又陷入四分五裂的局面，进入了五代十国时期。“五代”指的是（        ） C．因文字犯罪被捕入狱 D．为加强文化专制而设立的监狱 A．后梁、后唐、后晋、后汉、后周 B．后宋、后齐、后梁、后陈、后周 19．我国封建社会的人丁税最后废止于（        ） C．东威、西魏、北齐、北周、东晋 D．西夏、金、北宋、南宋 A．顺治年间 B．康熙年间 C．雍正年间 D．乾隆年间 7．“苏湖熟，天下足"的谚语说明南宋时（        ） 20．明清时期，传入中国并得到推广种植的高产作物是（        ） A．北方战乱不息，南方相对安定 B．太湖流域已成为全国的粮仓 A．核桃 B．棉花 C．双季稻 D．玉米 C．封建政府对农民的剥削十分沉重 D．江南的自然条件优越于北方 二、辨析改错题（本大题共5小题，共10分） 8．北宋时期，随着农业的发展，手工业也发展起来，其中北宋兴起的景德镇，后来发展成为著名的（        ） 21．辨别下列史实的正误，在题前括号内正确的打“√”；错误的打“×”，并加以改正。 A．丝绸之乡 B．鱼米之乡 C．瓷都 D．产茶中心 （1）隋文帝时设进士科，标志着科举制正式确立。 9．交子是世界上最早的纸币，它出现于北宋前期的（        ） A．开封地区 B．江南地区 C．四川地区 D．洛阳地区 【】改正：________ 10．如图中的历史人物少有大志，“思大有为于天下”。他一生征战，一统天下，建立幅员广阔的统一多 （2）宋朝的海外贸易超过前代，近至朝鲜日本，远达阿拉伯半岛和非洲西海岸。 民族国家。关于他的说法正确的是（        ） 【】改正：________ ①建立元朝 ②统一蒙古 ③灭掉南宋 ④废除丞相 （3）从唐朝中期开始的经济中心南移，到北宋时最后完成。 【】改正：________ A．①②③ B．①②③④ （4）元代最优秀的杂剧作家时马致远，代表作是悲剧《窦娥冤》。 C．①② D．①③ 11．许多发明创造就是普通人经过辛辛苦苦的探索而得来的，北宋时期平民毕昇发明了（        ） 【】改正：________ A．雕版印刷术 B．活字印刷术 C．指南针 D．火药 （5）1684年清政府设台湾府，隶属福建省，加强了中央政府对台湾的管辖，巩固了祖国的东南海防。 12．某学习小组开展研究性学习，整理出以下史实：郑成功收复台湾、清政府设立驻藏大臣、乾隆帝平定 【】改正：________ 大小和卓叛乱，如果要给他们的研究确定一个主题，应该是（        ） A．国家的巩固与发展 B．文化的繁荣与昌盛 三、材料解析题（本大题共2小题，共26分） C．机构的设置与变化 D．对外的联系与交往 22．同学们，通过一年的学习之后，想了解你们对中国古代政治史学习的情况和感受。（14分） 第1页，共4页 第2页，共4页']}

query_json_spell_3 = {'subject':'history', 'query':
                      ['2019—2020学年第二学期期末评估试卷 6．澶渊之盟后，宋辽边境“生育蕃息，牛羊被野（遍地），戴白之人，不识干戈（战争）” 这说明澶渊之盟 七年级历史 A．维持了宋辽间的长久和平 B．实现宋辽双方的完全平等 C．直接导致南方经济的繁柴 D．使北宋军事力量完全瓦解 叩 注意事项： 7．有一位历史人物与“精忠报国”“还我河山”“郾城大捷”有关，此人是 1、本试卷共6页，分为选择题和非选择题，满分50分. 2、开卷考试，可查阅资料，但应独立答题，禁止交流资料。 A．文天祥 B．岳飞 C．郑成功 D．渥巴锡 3、本试卷上不要答题，请按答题卡上注意事项的要求直接把答案填写在答题卡上。答在 8．《元史》评价成吉思汗“帝深沉有大略，用兵如神，故能灭国四十，遂平西夏。其奇勋 试卷上的答案无效。 伟迹甚众，惜乎当时史官不备，或多失于纪载云。”成吉思汗的主要事迹是 体 掷 第一部分选择题（共20小题，20分） A．统一蒙古各部 B．联宋灭金 米 下列每小题列出的四个选项中，只有一项是最符合题目要求的。请将正确选项的英文字母 C．建立元朝 D．灭南宋统一企国 代号涂写在答题卡相应位置上。 9．司马光和司马迁，被后人称为“史学两司马”。北宋著名史学家司马光主持编写的，并 1．下列哪一史实结束了长期分裂的局面，顺应了我国统一多民族国家的历史发展大趋势 由宋神宗以“鉴于往事，有资于治道”赐名的史学巨著是 A．隋文帝灭掉陈朝 B．隋朝创立科举制 A．《战国策》 B．《新五代史》 C．《史记》 D．《资治通鉴》 C．隋朝统一度量衡 D．隋朝开通大运河 10．《明史•宋濂传》记述：大学士宋濂上朝，朱元璋问他昨天在家请客没有，客人是谁， 国 $ 2．历史叙述有历史陈述、历史评价等方式。其中，历史评价是指对历史现象和历史事实 吃的什么菜，宋濂一一照实回答，朱元璋很满意说：“你没有欺骗我。”这一记载可以用于研究 进行态度与价值的评判表述。下列选项属于历史评价的是 A．朱元璋提倡尊孔崇儒 B．明初大大强化皇权 都 A．汉武帝在长安兴办太学，大力推行儒学教育 C．明朝的君臣关系和睦 D．明初朝臣权力过大 B．“贞观之治”和“开元盛世”都是中国古代治世 11．明朝时期著名的丝织业中心和制瓷中心分别是 C．由越南传入的占城稻成熟早，抗旱力强，北宋时推广至东南地区 A．海南岛、定窑 B．开封、汝瓷 C．苏州、景德镇 D．南京、哥窑 救 D．清朝雍正皇帝设置了军机处 12．2020年春，一场突如其来的新型冠状病毒从武汉迅速向全国蔓延。在疫情防治中，中 3．2020年初国内新冠肺炎疫悄发生后，引起了世界各国人民的关注。日本迅速募集物资 医药发挥了很大作用。下列可以给我们提供医疗和防治帮助的中医著作是 驰援，日本汉语水平考试HSK事务捐赠的驰援物资包装箱上用中文写有“山川异域，日月同天”， A．《天工开物》 B．《农政全书》 C．《齐民要术》 D．《本草纲目》 寄托了日本人民的深情厚谊。在唐代，也有一段中日友好交往的佳话，它是 13．李自成领导的农民起义军提出“均田免赋”的口号，受到广大农民的热烈欢迎。其根本 抑 A．张骞出使西域 B．文成公主入藏 原因是 补 C．鉴真东渡 D．玄奘西行 A．倭寇猖獗，外患严重 B．农民觉悟高，拥护起义军 4．唐朝从“小邑犹藏万家室”到“人烟断绝，千里萧条”的转折点是 C．经济发展，出现商帮 D．明末政治腐败，赋税沉重 A．开凿运河 B．安史之乱 C．黄巢起义 D．靖康之变 14．“从戚继光抗倭到郑成功收复台湾再到雅克萨之战，从册封达赖、班禅到设置驻藏大 5．多数谚语反映了当时人民的生活实践经验。宋初有谚语曰：“做人莫做军，做铁莫做针。” 臣再到设置伊犁将年”。如果给上述史实提炼一个主题，较为合理的是 这说明当时社会 A．国家的巩固与发展 B．文化的碰撞与交流 u A．重武轻文 B．重视科学 C．重文轻武 D．重视商业 C．外交的开放与危机 D．经济的繁荣与稳定 七年级历史第1页（共6页） 七年级历史第2页（共6页）']}
# 符号混用方法检验； 空格过多校验；错词功能那个检验；繁简字检验；
query_json_zh_2 = {'grade': 'senior', 'subject': 'history', 'query': {
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
    "difficulty": 0.1, "type": "材料分析题"}}



query2 = {"grade": "senior",
    "subject": "physics",
    "query":{"_id": 3239703295.0, "description": "如图的折现图示某农村小卖部【&】年一月份至五月份的营业额与支出数据，根据该折线图，下列说法正确的是()",
             "stems": [{"options": {"A": "农业生产", "B": "家庭生活", "C": "交通堵塞", "D": "军事战争"}, "stem": "（1）图示的天气对人类的影响是（        ）"},
                       {"options": {"A": "台风", "B": "沙尘暴", "C": "洪水", "D": "暴风雪"}, "stem": "（2）图示天气是（        ）"}],
             "labels": ["天气及其影响"],
             "answers": ["C", "D"],
             "solutions": ["（1）由图可知，此天气是发生暴风雪，导致交通堵塞。故选D。", "（2）由图可知，图示天气是暴风雪。故选D。"],
             "explanations": ["（1）天气和气候与人类生活、生产关系十分密切，学习时要认真理解。", "（2）结合图来解答即可。"],
             "difficulty": 0.9, "type": "选择题"}}


def api_test(query):
    # url = 'http://0.0.0.0:9559/text_quality_check'
    url = 'http://172.18.1.117:9760/text_quality_check'
    # url = 'http://172.18.1.117:9779/tqc_spell_check'
   # url = 'http://10.12.20.17:9760/text_quality_check'
    # url = 'http://yj-ctb-tqc.haofenshu.com/text_quality_check'
    begin = time.time()

    r = requests.post(url, data=json.dumps(query))
    print(r.status_code)
    result_data = json.loads(r.text)
    print(result_data)
    print(time.time() - begin)


if __name__ == '__main__':
    api_test(query2)

