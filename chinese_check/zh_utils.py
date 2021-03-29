#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/11/4 10:52
# @Author : dyu
# @File : utils_old.py

import re
import time
import json
from collections import OrderedDict
import operator as op
from langconv import *
from collections import OrderedDict, Counter

################################# Global Quantitative ###################################
special = "“”’‘《》（）【】{}()[]<>"
opts_map = {0:'A', 1:'B', 2:'C', 3:'D', 4:"E", 5:"F", 6:"G", 7:"H", 8:"I", 9:"J"}
BRANKETS = {'}':'{',
            ']':'[',
            ')':'(',
            '”':'“',
            '’':'‘',
            '）':'（',
            '】':'【',
            '》':'《'}

FIND_LIST = ['n','nz','PER','LOC','ORG','s', 'nw','vn','a','an']
PUNCTUATION = '＂＃＄％＆＇（）＊＋，－／：；＜＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､　、〃〈〉《》' \
              '「」『』【】&^$#@!*〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏﹑﹔·！？｡。$、{}~%、\/,，'
ANSWER_LIST = ['见解答','详细见解答','如解答所示','答案见解答','如解答图所示',
               '详见解答','见解析','详情见解答','示意图如解答图所示','详解见解答','解：见解答',
               '答案如解答所示','推导过程见解答','答案如图所示','推导过程如解答所示']
BRANKETS_LEFT, BRANKETS_RIGHT = BRANKETS.values(), BRANKETS.keys()

EXCLUSIVE_LIST = ['有误','代尺','图尺','交往','外因','任写','下面','下类','下列','下表','宛转','新兴',
                  '实仰', '突显', '执著', '型塑', '逾发','图示', '小名', '天量']
STOP_CHAR = ['的','得','地','他', '她', '你','妳','我','但','砲','小','大','甲','乙','丙','多','少']
DIGIT = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九','十', '百', '千']

SYM_MAP = {'×': ['×', '错误', '不正确', 'times', '错','F','B'],
           '√': ['√', '正确','A','T'], 
           '错误': ['错误', '不正确', 'times','F','×','B','错',],
           '不正确': ['不正确', '错误', 'times','F','B','错','×'],
           '正确': ['正确','A','T','√'], 
           'times': ['×', '错误', '不正确', 'times','F','B','错'],
           '不对': ['错', '不正确', '错误', 'times','F','×','B'],
           '对': ['对', '正确','A','T','√'], 
           '错': ['错误', '不正确', 'times','F','错','B'],
           }

SYM_SIM = {'×': ['×', '错误', '不正确', 'times', '错'],  '√': ['√', '正确'],
            'times': ['×', '错误', '不正确', 'times'],
           '正确':['√','对','正确'],
           '不正确':['不正确','错误','times','错','×'],
           '错误':['错误','不正确','times','错','×']}

ANTONYM_MAP = {'×': ['正确', '√'], 'T': ['错误', 'F'], '√': ['×', '错误', '不正确'], '错误': ['正确'], '不正确': ['正确'],
               '正确': ['不正确', '错误'], 'F': ['T', '正确'], 'times': ['√', '正确'], '不对': ['对', '正确'], '对': ['错误', '不正确'],
               '错': ['正确', '对']}

FW_ALPHABET = ['Ａ','Ｂ','Ｃ','Ｄ','Ｅ','Ｆ','Ｇ','Ｈ','Ｉ','Ｊ','Ｋ','Ｌ','Ｍ','Ｎ','Ｏ','Ｐ','Ｑ','Ｒ','Ｓ','Ｔ','Ｕ','Ｖ','Ｗ','Ｘ','Ｙ','Ｚ']

ALPHABET_DICT = {'Ａ':'A', 'Ｂ':'B', 'Ｃ':'C','Ｄ':'D', 'Ｅ':'E', 'Ｆ':'F', 'Ｇ':'G', 'Ｈ':'H', 'Ｉ':'I', 'Ｊ':'J',
                     'Ｋ':'K', 'Ｌ':'L', 'Ｍ':'M', 'Ｎ':'N', 'Ｏ':'O', 'Ｐ':'P', 'Ｑ':'Q', 'Ｒ':'R', 'Ｓ':'S', 'Ｔ':'T',
                     'Ｕ':'U', 'Ｖ':'V', 'Ｗ':'W', 'Ｘ':'X', 'Ｙ':'Y', 'Ｚ':'Z'}
############################################################################################


def read_json(js_f):
    """ 读json """
    with open(js_f, 'r', encoding='utf8') as f:
        phy_dict = json.load(f, object_pairs_hook=OrderedDict)
    return phy_dict


def save_json(data, js_f):
    """ 保存json """
    with open(js_f, 'w', encoding='utf8') as f:
        json.dump(data, f, ensure_ascii=False)


def is_Chinese(word):
    """ 判断是否为中文 """
    for ch in word:
        if '\u4e00' <= ch <= '\u9fff' or ch == '\ufeff':
            return True

    return False


def Chinese_conversion(sentence, Trad2Sim=True):
    '''
    将sentence中的繁体字转为简体字 Traditional2Simplified or Simplified2Traditional
    :param sentence: 待转换的句子
    :param Trad2Sim: 繁转简（defalut）
    :return: 将句子中繁体字转换为简体字之后的句子
    '''
    if Trad2Sim:
        sentence = Converter('zh-hans').convert(sentence)
    else:
        sentence = Converter('zh-hant').convert(sentence)
    return sentence


def num_to_ch(num):
    """
    功能说明：将阿拉伯数字 ===> 转换成中文数字（适用于[0, 10000)之间的阿拉伯数字 ）
    """
    num = str(num)
    num_list = []
    _convert = {''}
    _MAPPING = {'0': '零', '1': '一', '2': '二', '3': '三', '4': '四', '5': '五',
                '6': '六', '7': '七', '8': '八', '9': '九'}
    FH_NUM = {u"０": u"0", u"１": u"1", u"２": u"2", u"３": u"3", u"４": u"4",
              u"５": u"5", u"６": u"6", u"７": u"7", u"８": u"8", u"９": u"9"
              }
    for ch in num:
        if ch in FH_NUM:
            ch = FH_NUM[ch]
        num_list.append(_MAPPING[ch])
    return ''.join(num_list)


def postProcess(orig_char, corr_char):
    if (orig_char not in PUNCTUATION) & (corr_char not in PUNCTUATION) & \
            (not (orig_char.isdigit() | corr_char.isdigit())):
        if (orig_char not in STOP_CHAR) & (orig_char not in DIGIT):
            if is_Chinese(orig_char):
                return True


def findSpace(string):
    value = re.findall(r'(.* {1,}.*)', string)

    if len(value)>0:
        value = re.sub(r'(\s)', '', string)
        return value
    else:
        return string


def preprocess(data):
    data = re.sub(r'[a-zA-Z]', '&', data)
    data = re.sub(r'(_+)', '&', data)
    data = re.sub(r'(\（\d+\）)', '', data)
    data = re.sub(r'(\(\d+\))', '', data)
    data = re.sub(r'[\s\t\n\xa0]', '', data)
    data = re.sub(r'[.]', '', data)
    data = findSpace(data)
    return data


def latex_process(text):
    pattern = re.compile(r'\$.+?\$')
    if len(re.findall(pattern, text)) > 0:
        text = re.sub(r'[\(${\\)\}$]', '', text)
    return text


def getnestList(lst, change=False):
    """
    递归嵌套list
    :param lst:
    :return:
    """
    res = list()
    for element in lst:
        if not isinstance(element, list):
            res.append(element)
        else:
            res.extend(getnestList(element))
    if change:
        return ''.join(res)
    else:
        return res


def find_max_sub(pattern, data):
    """
    找到最大的小题号
    :param pattern:  re pattern
    :param data:
    :return:
    """
    if re.findall(pattern, getnestList(data, True)):
        ans_subs = re.findall(pattern, getnestList(data, True))
        return max(ans_subs)
    else:
        return data


def check_full_width(text):
    """
    检查文本是否存在全角半角混用
    """
    
    for fw in FW_ALPHABET:
        if fw in text:
            text = ''.join(process_latin(list(text)))
            # if re.search(r'[a-zA-Z]',text) != None:
            #     return False
    return text


def process_latin(alphabet_list):
    '''
    全半角统一转换成半角
    '''

    for i in range(len(alphabet_list)):
        if alphabet_list[i] in ALPHABET_DICT.keys():
            alphabet_list[i] = ALPHABET_DICT[alphabet_list[i]]
    return alphabet_list


def pump_list(para):
    """ 抽list """
    while True:
        if isinstance(para, list) and len(para) == 1:
            para = para[0]
        else:
            break
    return para


def pump_list_to_str(sentence):
    sentence = pump_list(sentence)
    if isinstance(sentence, list):
        cont = ''
        for ans in sentence:
            if isinstance(ans, dict):
                ans = json.dumps(ans, ensure_ascii=False)
            elif isinstance(ans, list):
                an =''
                for a in ans:
                    an+=a+'\t'
                ans = an
            else:
                ans = ''.join(pump_list(ans))
            cont += pump_list(ans)+'\n'
        sentence = cont
    else:
        sentence = ''.join(sentence)
    return sentence


def checkLetter(answer):
    """ 检测选项是否含有ABC """
    value = []
    if type(answer) == list:
        for ans in answer:
            if type(ans) == list:
                a1 = ''.join(ans)
                value = re.findall(r'[a-zA-Z]', a1)
            else:
                ans = ''.join(ans)
                value = re.findall(r'[a-zA-z]',ans)
    elif type(answer) == str:
        value = re.findall(r'[a-zA-Z]', answer)
    else:
        pass
    return value


def bracket(_string):
    """ 检测括号符号匹配 """
    stack_left = []
    stack_right = []
    for i, char in enumerate(_string):
        # 如果是左括号
        if char in BRANKETS_LEFT:
            # 入栈
            stack_left.append((i, char))
        # 右括号
        elif char in BRANKETS_RIGHT:
            # # stack不为空，并且括号匹配成功
            # if stack:
            #     # 出栈
            flag = False
            for st in reversed(stack_left):
                if st[1] == BRANKETS[char]:
                    stack_left.remove(st)
                    flag = True
                    break
            if not flag:
                stack_right.append((i, char))
            # 匹配成功
            # else:
            #     return False, stack+stack_right
    stack = stack_left+stack_right
    return not stack, stack


def split_sentence(para):
    """
    中文分句(定制)
    :param para:
    :return:
    """
    """ 1.单字符断句符 """
    para = re.sub('([。！？\?])([^”’}\]】])', r"\1@@\2", para)

    """ 2.英文省略号&中文省略号 """
    para = re.sub('(\.{6})([^”’])', r"\1@@\2", para)  # 英文省略号
    para = re.sub('(\…{2})([^”’])', r"\1@@\2", para)  # 中文省略号

    """ 3.去除引号里的@@分隔符 """
    p1 = re.compile(r"(.*[\“\‘])(.*)(@{2,})(.*[\”\’].*)")
    if '@@' in re.findall(r"[\“\‘].*(@{2,}).*[\”\’]", para):
        para = re.sub(p1, r"\1\2\4", para)

    """ 4.如果双引号前有终止符，那么双引号才是句子的终点，把分句符@@放到双引号后，注意前面的几句都小心保留了双引号 """
    para = re.sub('([。！？\?][”’}\]】])([^，。！？\?])', r'\1@@\2', para)

    """ 5.判断找到[【{}】]里的 分割符，并不切分 """
    p2 = re.compile(r'(.+[\[【{].*)(@{2,})(.*[}】\]].+)')
    if "@@" in re.findall(r'.+[\[【].*(@{2,}).*[】\]].+', para):
        para = re.sub(p2, r"\1\3", para)

    # para = para.rstrip()  # 段尾如果有多余的\n就去掉它
    para = para.split('@@')
    return para


def read_json(path):
    content_list = []
    with open(path, 'r', encoding='utf-8') as f:
        data = f.readlines()
        for d in data:
            phy_dict = json.loads(d)
            content_list.append(phy_dict)
    return content_list


def getChineseStopWord():
    """获取stopwords"""
    stop_word = []
    with open('chinese_check/zh_data/stopword_20201124.txt', 'r', encoding='utf-8') as f :
        content = f.read().split('\n')
        for c in content:
            stop_word.append(c.strip())
    return stop_word


def get_recursively_list(list_name):
    """
    Process recursively list
    递归处理嵌套列表找出最小元素
    """
    processed_list = []
    def Recursively_List(list_name):
        for i in list_name:
            if isinstance(i,list):
                Recursively_List(i)
            else:
                processed_list.append(i)
    Recursively_List(list_name)
    return processed_list


def match(answer, sym):

    if answer == sym:
        return True
    elif answer.startswith('判断'):
        if answer[answer.index('判断'):].rfind(sym) != -1:
            return True
    else:
        return False


def checkSymbol(answer, special = None, value_list = None):
    answer = str(pump_list(answer))
    flag = False
    if special:
        if value_list is not None:
            specialList = list(SYM_SIM.keys())+ value_list
        else:
            specialList = SYM_SIM.keys()

        for sym in specialList:
            if match(answer, sym):
                return True
    else:
        if value_list is not None:
            specialList = list(SYM_MAP.keys())+value_list
        else:
            specialList = SYM_MAP.keys()

        for sym in specialList:
            if match(answer, sym):
                return True


def is_have_sub(text):
    """
    判断题干中是否含有小题
    :param text:
    :return:
    """
    # p = re.compile(r'[（\(]\d+[）\)] | [①②③④⑤⑥⑦⑧⑨⑩]')
    p = re.compile(r'[（\(]\d+[）\)]')
    if isinstance(text, str):
        if re.findall(p, text):
            sub = re.findall(p, text)
            return sub, len(sub)
    else:
        sub = [re.findall(p, t)[0]  for t in text if re.findall(p, t)]
        return sub, len(sub)


def decompose(item):
    """
    分解题型, 只针对目前数据形式
    :return:
    """
    question = item['question']
    answers = item['answers']
    solutions = item['solutions']
    opts = item['opts']
    _type = item['type']
    labels = item['labels']
    explanations = item['explanations']  # 暂不做分析
    return question, opts, answers, solutions, _type


def format_error_check(text, subject=None):
    """
    Find format error
    :return:
    """
    if text['type'] == "选择题":
        if text['opts'][0] is '' or text['opts'][0]['A'] is '' or len(text['opts']) == 0:
            return False
        else:
            return True


def remove_latex_of_text(text):
    """
    去除latex公式
    :param text:
    :return:
    """
    latex_p = re.compile(r"(\$\{.*?\}\$)")
    if isinstance(text, str):
        D_latex_text = re.sub(latex_p, '', text)
        return D_latex_text
    else:
        D_latex_text = re.sub(latex_p, '', str(text))
        return eval(D_latex_text)


def serial_matching(text):
    """
    序号要匹配 ①②③④ or (1)(2)(3)等, 题干中小题号排序正确和答案对应;
    适用范围 全题型
    1、判断科目
    2、判断题型
    :parameter text :
    :return Error_set:
    """
    question, opts, answers, solutions, _type = decompose(text)
    Error_set = list()  # 错误集合
    opts_map = {0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: "E", 5: "F", 6: "G", 7: "H", 8: "I", 9: "J"}
    isdigit = False

    question = remove_latex_of_text(question)
    answers = remove_latex_of_text(answers)
    solutions = remove_latex_of_text(solutions)

    ### 判断是否格式有问题
    if format_error_check(text):
        ### Situation1 如果题干中有（1）（2）|(1)(2)，判断选项、答案、解答中是否有超出序号
        p1 = re.compile(r'[（\(]\d+[）\)]')
        ### ！！！如果进行此步骤，请去除latex公式
        if len(re.findall(p1, question)) != 0:
            sub_question = re.findall(p1, question)  #
            Q_max_sub = max(sub_question)  # 最大序号
            # 判断答案中小题题号是否超出序号
            if re.findall(p1, getnestList(answers, True)):
                ans_subs = re.findall(p1, getnestList(answers, True))
                if max(ans_subs) > Q_max_sub:
                    Error_set.append((answers, 'zh_sub_q_unmatch_error'))

            # 判断解答中小题题号是否超出序号
            if re.findall(p1, getnestList(solutions, True)):
                solu_subs = re.findall(p1, getnestList(solutions, True))
                if max(solu_subs) > Q_max_sub:
                    Error_set.append((answers, 'zh_sub_q_unmatch_error'))
            isdigit = True

        ### Situation2 如果题干中有①②③④⑤⑥⑦⑧⑨⑩，判断选项、答案、解答中是否有超出序号
        p2 = re.compile(r'[①②③④⑤⑥⑦⑧⑨⑩]')
        if len(re.findall(p2, question)) != 0:
            # 1、校验题干, 作为标准
            labels = re.findall(p2, question)
            max_num = max(labels)
            # 2、校验选项, 除选择题外都不做校验
            if _type == '选择题':
                for k, v in opts[0].items():
                    if len(re.findall(p2, v)) != 0:
                        if max(re.findall(p2, v)) > max_num:
                            Error_set.append(('选项' + k, 'zh_sub_q_unmatch_error'))

            isdigit = True
            # 3、答案校验，除选择题外都做校验
            if _type != '选择题':
                if isinstance(answers, list):
                    for i, l in enumerate(answers):
                        ans_str = re.findall(p2, ''.join(pump_list(l)))
                        if len(ans_str) != 0:
                            if max(ans_str) > max_num:
                                Error_set.append(('答案' + opts_map[i], 'zh_sub_q_unmatch_error'))

                isdigit = True
            # 4、校验解答
            if isinstance(solutions, list):
                if len(solutions) > 1:
                    for i, solu in enumerate(solutions):
                        if len(re.findall(p2, solu)) != 0:
                            if max(re.findall(p2, solu)) > max_num:
                                Error_set.append(('第{}个解答'.format(i + 1), 'zh_sub_q_unmatch_error'))
                        isdigit = True
                        
                elif len(solutions) == 1 and ';' or '；' or '。' in solutions:
                    solutions = re.split(r"[;；。]", solutions[0].strip())
                    for i, solu in enumerate(solutions):
                        if len(re.findall(p2, solu)) != 0:
                            if max(re.findall(p2, solu)) > max_num:
                                Error_set.append(('第{}个解答'.format(i + 1), 'zh_sub_q_unmatch_error'))
                        isdigit = True
                else:
                    pass
    else:
        p1 = re.compile(r'[（\(]\d+[）\)]')
        p2 = re.compile(r'[①②③④⑤⑥⑦⑧⑨⑩]')
        if len(re.findall(p1, question)) != 0 or len(re.findall(p2, question)) != 0 or \
                len(re.findall(p1, getnestList(answers, True))) != 0 or len(
            re.findall(p2, getnestList(answers, True))) != 0 or \
                len(re.findall(p1, getnestList(solutions, True))) != 0 or len(
            re.findall(p2, getnestList(solutions, True))) != 0:
            isdigit = True
    return isdigit

def sortList(tuple_list, value_list):
    value_result = []
    result = tuple_list.copy()
    result.sort(key=lambda x: x[0])
    if (value_list is not None) and (len(value_list)>0):
        for value in result:
            value_result.append(value_list[tuple_list.index(value)])
    return value_result, result



def show_text_value(value_list, text):
    position = []
    for r in value_list:
        if isinstance(r[0], int) & isinstance(r[1], int):
            r0 = r[0]
            r1 = r[1]
        else:
            r0= int(r[0])
            r1 = int(r[1])

        if ((r0- 4) > 0) & ((r1+ 4) < len(text)):
            position += text[r0 - 4: r1 + 4]
        elif ((r0 - 4) < 0) & ((r1 + 4) < len(text)):
            position += text[0: r1 + 4]
        elif ((r0 - 4) > 0) & ((r1 + 4) > len(text)):
            position += text[r0 - 4:]
    return position


def simple_serial_matching(answer):
    p1 = re.compile(r'[（\(]\d+[）\)]')
    isdigit = False
    if len(re.findall(p1, answer)) != 0:
        isdigit = True
    return isdigit


def qa_matching(answer, solution, subject=None):
    """
    问题与答案匹配对应校验
    :param tid_dict:
    :return:
    """
    global SYM_SIM
    key_words = {'故说法', '故本题', '因此本题', '故此题', '故题干', '所以题干', '题干说法', '题干的叙述', '故答案为：', '故命题', '故', '因此', '因此题干', '说法是',
                 '这种说法','此题说法'}
    result_dict = dict()  # 结果result
    # 没有小题的情况

    if subject =='地理':
        SYM_SIM.update({'对': ['对', '正确','A','T','√'], '错': ['错误', '不正确', 'times','F','错','B']})
    elif subject == '生物':
        SYM_SIM.update({'T': ['T', '正确', 'A', '√'],'F': ['F', '错误', '不正确', 'times', '×', '错', 'B']})

    if len(answer) == 1 and len(solution) == 1:
        answer = get_recursively_list(answer)
        solution = get_recursively_list(solution)
        answer = answer[0]
        solution = solution[0]
        count = 0
        for sym in SYM_SIM.keys():
            if sym in answer:
                count += 1
                syns_list = SYM_SIM[sym]
                antonym_list = ANTONYM_MAP[sym]
                index_a = list()
                for k in key_words:
                    if solution.rfind(k) != -1:
                        index_a.append(solution.rfind(k))
                        break
                if len(index_a) > 0:
                    for syn in syns_list:
                        if syn in solution[index_a[0]:]:
                            return result_dict
                    for antonym in antonym_list:
                        if antonym in solution[index_a[0]:]:
                            result_dict['errorType'] = 'zh_answer_unmatch_error_1'
                            result_dict['description'] = 'answer与solution不对应'
                            return result_dict

                    result_dict['errorType'] = 'zh_answer_unmatch_error_1'
                    result_dict['description'] = 'solution匹配不到symbol'
                    return result_dict
                else:
                    result_dict['errorType'] = 'zh_answer_unmatch_error_1'
                    result_dict['description'] = 'solution匹配不到关键字'
                    return result_dict
        if count > 0:
            return result_dict
        else:
            # result_dict['errorType'] = 'zh_answer_unmatch_error'
            # result_dict['description'] = 'answer匹配不到symbol,题型：判断题'
            return None

    # 有小题的情况
    else:
        if len(answer) == len(solution) > 1:
            answer = get_recursively_list(answer)
            solution = get_recursively_list(solution)
            ans_sym_list = []
            for ans in answer:
                for sym in SYM_SIM.keys():
                    if sym in ans:
                        ans_sym_list.append(sym)
                        break
            if len(ans_sym_list) == len(answer):
                for i, ans_sym in enumerate(ans_sym_list):
                    solution = solution[i]
                    antonym_list = ANTONYM_MAP[ans_sym]
                    syns_list = SYM_SIM[ans_sym]
                    index_b = list()
                    for k in key_words:
                        if solution.rfind(k) != -1:
                            index_b.append(solution.rfind(k))
                            break
                    if len(index_b) > 0:
                        for syn in syns_list:
                            if syn in solution[index_b[0]:]:
                                return result_dict
                        for antonym in antonym_list:
                            if antonym in solution[index_b[0]:]:
                                result_dict['errorType'] = 'zh_answer_unmatch_error_1'
                                result_dict['description'] = 'answer与solution不对应'
                                return result_dict

                        result_dict['errorType'] = 'zh_answer_unmatch_error_1'
                        result_dict['description'] = 'solution匹配不到symbol'
                        return result_dict
                    else:
                        result_dict['errorType'] = 'zh_answer_unmatch_error_1'
                        result_dict['description'] = 'solution匹配不到关键字'
                        return result_dict
            else:
                return None
        else:
            return None


if __name__ == "__main__":
    case1 = "为了检验词汇分割的效果…… 我们可以“使用词语！错误.率。”+-*(word error rate)来衡量。"
    case2 = "菲利普·费尔南德兹·阿迈斯托在评价某科学家时。指出：在他的宇宙里，“每一种现象都是带有欺骗性。物质和能量可以相互转换，双胞胎以不同的速度衰老，平行线可以交叉，光线弯曲的径迹其实缠绕宇宙。”这位科学家是【爱因斯坦】.阿斯蒂芬。nihao!"
    case3 = "【（1）变化：不断减少。】（2）结合所学知识，【分析上述“变化出现。”的】主要原因。【（2）主要原因：苏俄（联）实行新经济政策（或以固定的粮食税取代余粮征集制）。】"
    case4 = "环境保护部审议并通过的《环境空气质量标准》，首次制定PM2.5（指大气中可入肺的颗粒物）的国家环境质量标准。广东省珠三角成为我国第一个按照新标准监测并评价空气质量的城市群。这说明我国（        ）"
    case5 = "吉林市对600名中学生进行过一次采用问卷和访谈等方式的调查，当问及“业余时间最喜欢和谁在一起”时，80.7%的学生回答是同伴。调查显示，身为独生子女的中学生更重视同学间的友谊。\t（1）此调查结果说明了什么？\t（2）如何与同学、伙伴交往和沟通？\t（3）在与同学、伙伴交往中，如何建立和维护友谊？"
    case6 = "在${\\triangle ABC}$中，${\\angle ACB= 90^{{\\circ} }}$，${AC= BC}$，直线${MN}$经过点${C}$，且${AD\\perp MN}$于${D}$，${BE\\perp MN}$于${E}$，求证：${DE= AD+ BE}$．【证明：∵${\\angle ACB= 90^{{\\circ} }}$，${AC= BC}$，∴${\\angle ACD+ \\angle BCE= 90^{{\\circ} }}$，又∵${AD\\perp MN}$，${BE\\perp MN}$，∴${\\angle ADC= \\angle CEB= 90^{{\\circ} }}$，而${\\angle ACD+ \\angle DAC= 90^{{\\circ} }}$，∴${\\angle BCE= \\angle CAD}$．在${\\triangle ADC}$和${\\triangle CEB}$中，∵${\\left\\{ {\\begin{matrix} {\\angle CAD= \\angle BCE} \\\\ {\\angle ADC= \\angle CEB} \\\\ {AC= BC} \\end{matrix}} \\right.}$，∴${\\triangle ADC\\cong \\triangle CEB( AAS)}$．∴${AD= CE}$，${DC= EB}$．又∵${DE= DC+ CE}$，∴${DE= EB+ AD}$．】"
    # print("Result:", split_sentence(case3))
    case7 = {"_id": 2065825791, "question": "家兔细胞中的能量转换器是线粒体和叶绿体。________（判断对错）", "opts": [""], "labels": ["线粒体和叶绿体是细胞中两种能量转换器"], "answers": [["F"]], "solutions": ["解：植物细胞的结构有细胞壁、细胞膜、细胞质、细胞核、液泡、叶绿体和线粒体等，动物细胞有细胞膜、细胞质、细胞核和线粒体等。细胞中的能量转换器是叶绿体和线粒体，动物细胞只有线粒体，没有叶绿体。故本题说法错误。"],"explanations": ["细胞中的能量转换器是叶绿体和线粒体，植物细胞有叶绿体和线粒体，动物细胞只有线粒体。进行解答。"], "difficulty": 0.6, "type": "判断题"}

    print(qa_matching(case7))


