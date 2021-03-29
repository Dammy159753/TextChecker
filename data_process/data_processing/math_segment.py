# !/usr/bin/python3
# -*- coding:utf-8 -*-
# @Author : dengyu
# @Time   : 2020-03-27 20:17

import re, os, json, nltk, jieba
# import jieba_fast as jieba


# # Math Mainly formulaic word segmentation ###
class SegTool(object):
    def __init__(self, stopwords_path='dataset/stopword.txt', user_dict_path=None):
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
        paragraph = re.sub('(\.{6})([^”’])', r"\n", paragraph)  # 英文省略号
        paragraph = re.sub('(…{2})([^”’])', r"\n", paragraph)  # 中文省略号
        paragraph = re.sub('([。！？?][”’])([^，。！？?])', r'\n', paragraph)
        # 如果双引号前有终止符，那么双引号才是句子的终点，把分句符\n放到双引号后，注意前面的几句都小心保留了双引号
        paragraph = paragraph.rstrip()  # 段尾如果有多余的\n就去掉它
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
        # if COURSE in ['math', 'chemical', 'biology']:

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