# !/usr/bin/python3
# -*- coding:utf-8 -*-
# @Author : licheng
# @Time   : 2020-05-22 10:37

# ###########################################################################
# #               Senior math cleaner and word segment                    ###
# #                    1.源数据中重复和近似相近的数据                        ###
# #                    2.分词方法                                          ###
# ###########################################################################

import re, os, json, jieba, nltk
from data_processing.answer_filler import data_process


def read_json(js_f):
    with open(js_f, 'r', encoding='utf8') as f:
        phy_dict = json.load(f)
    return phy_dict


def save_json(data, js_f):
    with open(js_f, 'w', encoding='utf8') as f:
        json.dump(data, f, ensure_ascii=False)


class DealLaTex:

    def __init__(self, sym_path):
        self.sym_dct = read_json(sym_path)

    def process_latex(self, text):
        # 移除latex的开始与结束标记
        text = re.sub(r'\$', '', text)

        # 移除没有用的字符 <已加入词表>
        text = self.rm_mathrm(text)

        # 特殊字符替换
        text = self.sub_symbol(text)

        # 处理分式
        text = self.deal_formula(text)

        # 处理 ^ 跟 _
        text = self.underline_power(text)

        # 处理单独处理的特殊公式(先处理^ _)
        text = self.trans_special_symbol(text)

        # 格式整理
        text = self.unified_format(text)

        return text

    def rm_mathrm(self, text):
        text = re.sub(r'\\math[a-zA-Z]+', r'', text)
        return text

    def sub_symbol(self, text):
        # 特殊字符替换
        for latex, sym in self.sym_dct.items():
            text = text.replace(latex, sym)
        return text

    def deal_formula(self, text):
        # 处理分式
        while True:
            start_text = text
            text = re.sub(r'(\\d?frac *\{[^{}]*?)\{([^{}]+)\}(.*?\})', r'\1(\2)\3', text)
            if start_text == text:
                break
        text = re.sub(r'\\d?frac *\{(.*?)\} *\{(.*?)\}', r'{\1}/{\2}', text)
        text = re.sub(r'd?frac *(.) *(.)', r'\1/\2', text)
        return text

    def underline_power(self, text):
        # 处理 ^ 跟 _
        text = re.sub(r'([_\^]) *(?:\{(.*?)\}|([^{}]))', r'\1\2\3 ', text)
        text = re.sub(r' +([_\^].*?)', r'\1', text)
        return text

    def trans_special_symbol(self, text):
        # 处理度与摄氏度 circ
        text = re.sub(r'\^ *° *C', r'℃', text)
        text = re.sub(r'\^ *°', r'°', text)

        # 处理带反应条件的字符 overset
        text = re.sub(r'\\overset *\{([^{}]*?)\}\{(?:[\\=!]+|\\rightarrow)\}', r' 反应条件\1 ', text)
        text = re.sub(r'\\overset *\{\\frown *\}\{(.*?)\}', r'弧\1 ', text)
        text = re.sub(r'\\overset *', r'', text)
        return text

    def unified_format(self, text):
        """归一化格式"""

        # 花括号移除
        text = re.sub(r'\\\{', r'&&&$', text)
        text = re.sub(r'\\\}', r'$&&&', text)
        while True:
            start_text = text
            # 部分括号/花括号移除
            text = re.sub(r'\(([a-z0-9 ]*)\)', r'\1', text)
            text = re.sub(r'\(( *. *)\)', r'\1', text)
            # text = re.sub(r'\{([a-z0-9]*.)\}', r'\1', text)

            text = re.sub(r'\{([^{}]*?)\}', r' \1 ', text)
            if start_text == text:
                break

        text = re.sub(r'&&&\$', r'{', text)
        text = re.sub(r'\$&&&', r'}', text)

        # 移除多余空格
        text = re.sub(r'([^_−]) *', r'\1', text)
        text = re.sub(r' +', ' ', text)
        text = re.sub(r' *\^?°', r'°', text)
        text = re.sub(r' *([>·()/=×<~≤≥∠≠△⊥≡±∈～]+) *', r'\1', text)
        text = re.sub(r'\( *\)', '', text)

        text = text.replace('&gt;', '≥')
        text = text.replace('&lt;', '<')
        text = text.replace('&amp;', '')
        text = text.replace('&', '')

        text = re.sub(r'\\xrightarrow\[\\,\]', '', text)
        text = re.sub('cases(.*?)cases', r'分段函数\1', text)
        text = text.replace(r'\\\\', '或')
        text = text.replace('^′', '′')
        text = re.sub(r'\\', '', text)
        text = text.replace('，', ',')
        text = re.sub(r'([,。 ])+', r'\1', text)

        # ∫dx 定积分符号提取
        text = re.sub(r'∫(.*?)dx', r'定积分\1', text)

        # ^2 变成“二次方”
        text = re.sub(r'cm^\{2\}', '平方厘米', text)
        text = re.sub(r'\^2', '的二次方', text)
        return text


def truncate_sentence(sentence, left_symbol, right_symbol, max_len):
    """
    主要用来将过长的答案(left_symbol=【, right_symbol=】)、或句子(left_symbol=^, right_symbol=$)舍弃
    """
    pattern = re.compile(left_symbol + r'.*?' + right_symbol, re.S)
    target_sent = re.findall(pattern, sentence)
    sub_sentence = re.sub(pattern, '龏', sentence)

    pattern_rem = re.compile(r'[^龏]+')
    target_sent_rem = re.findall(pattern_rem, sub_sentence)
    sub_sentence = re.sub(pattern_rem, '龎', sub_sentence)

    i, j = 0, 0
    res_sentence = ''
    for index in range(len(sub_sentence)):
        flag = sub_sentence[index]
        if flag == '龏':
            temp_string = target_sent[i]
            if len(temp_string) > max_len:
                temp_string = ''
            res_sentence += temp_string
            i += 1
        else:
            temp_rem_string = target_sent_rem[j]
            res_sentence += temp_rem_string
            j += 1
    return res_sentence


def clean_text(questions_dct, labs):
    """
    预处理数学题目
    :param questions_dct: 可以为文件路径或者字典
    :return:
    """
    fill_answer = data_process(questions_dct, labs)
    deal_latex = DealLaTex(r'/media/chen2/dyu/SQR_training/src/dataset/new_latex_map.json')
    for index, key in enumerate(fill_answer.keys()):
        question = fill_answer[key]['question']
        question = deal_latex.process_latex(question)
        fill_answer[key]['question'] = question
    return fill_answer


# # Math Mainly formulaic word segmentation ###
class SegTool(object):
    def __init__(self, stopwords_path='/media/chen2/dyu/SQR_training/src/dataset/stopword.txt', user_dict_path=None):
        self.user_dict_path = user_dict_path
        if user_dict_path and not os.path.exists(user_dict_path):
            raise ValueError("File " + user_dict_path + " does not exist")
        elif user_dict_path:
            jieba.load_userdict(user_dict_path)
        if stopwords_path and not os.path.exists(stopwords_path):
            raise ValueError("File " + stopwords_path + " does not exist")
        self.stopwords = [line.strip() for line in open(stopwords_path, 'r', encoding='UTF-8').readlines()]

    def cutSent(self, paragraph):
        tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
        if "\xa0" in paragraph:
            paragraph = re.sub("(?:\xa0)+", ' ', paragraph).replace('\xa0', '')
        sentences4En = tokenizer.tokenize(paragraph)
        paragraph = re.sub('([。！？?])([^”’])', r"\n", paragraph)  # 单字符断句符
        paragraph = re.sub('(\.{6})([^”’])', r"\n", paragraph)      # 英文省略号
        paragraph = re.sub('(…{2})([^”’])', r"\n", paragraph)       # 中文省略号
        paragraph = re.sub('([。！？?][”’])([^，。！？?])', r'\n', paragraph)
        # 如果双引号前有终止符，那么双引号才是句子的终点，把分句符\n放到双引号后，注意前面的几句都小心保留了双引号
        paragraph = paragraph.rstrip()                              # 段尾如果有多余的\n就去掉它
        # 很多规则中会考虑分号;，但是这里我把它忽略不计，破折号、英文双引号等同样忽略，需要的再做些简单调整即可。
        sentences4Cn = paragraph.split("\n")
        return sentences4Cn if len(sentences4Cn) > len(sentences4En) else sentences4En

    def segWords(self, sentence):
        """
        分词，去停用词
        :param sentence:
        :return:
        """
        sentence = re.sub('[①②③④⑤⑥⑦⑧⑨∵∴；：，。！？?“”‘’]', ' ', sentence)
        sentence = re.sub('(\.{6})|(…{2})', ' ', sentence)
        sentence = re.sub(r'[【】]+', '', sentence.strip())
        sentence_depart = jieba.cut(sentence)
        result = []
        #if COURSE in ['math', 'chemical', 'biology']:
        
        # 结巴分词
        outStr = []
        # 去停用词后拼接 中文分词后的结果和非中文字符串
        unChineseStr = ''
        for word in sentence_depart:
            word = word.strip()
            if not '\u4e00' <= word <= '\u9fff':
                unChineseStr = unChineseStr + word
            else:
                if len(unChineseStr) >= 1:
                    outStr.append(unChineseStr)
                unChineseStr = ''
                outStr.append(word)
        if len(unChineseStr) >= 1:
            outStr.append(unChineseStr)
        for item in outStr:
            if item not in self.stopwords:
                if item and item != '\t':
                    result.append(item)

        if len(result) > 1:
            result = " ".join(result)
        return result

    def word_seg(self, query):
        """
        Word segment function 
        :param query :
        """
        sentences = self.cutSent(query)
        if len(sentences) == 1:
            result = self.segWords(sentences[0])
        else:
            result = self.segWords(" ".join(sentences))
        return result