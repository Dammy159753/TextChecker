# !/usr/bin/python3
# -*- coding:utf-8 -*-
# @Author : licheng
# @Time   : 2019-12-31 12:03
import re
import jieba
# import jieba_fast as jieba
from tqdm import tqdm

jieba.load_userdict('dataset/all_word_vocab.txt')
stopwords_path = 'dataset/stopword.txt'
stopwords = [line.strip() for line in open(stopwords_path, 'r', encoding='UTF-8').readlines()]

def get_latex(all_dct):
    latex_patten = re.compile(r'[^0-9\u4e00-\u9fa5]+')
    latex_dct = dict()
    for tid, item in tqdm(all_dct.items()):
        question = item['question']
        latex_lst = latex_patten.findall(question)
        for latex in latex_lst:
            latex_dct[latex] = latex_dct.get(latex, 0) + 1
    return latex_dct


def cut_sent(para):
    para = re.sub('([。！？?])([^”’])', r"\1\n\2", para)  # 单字符断句符
    para = re.sub('(\.{6})([^”’])', r"\1\n\2", para)  # 英文省略号
    para = re.sub('(…{2})([^”’])', r"\1\n\2", para)  # 中文省略号
    para = re.sub('([。！？?][”’])([^，。！？?])', r'\1\n\2', para)
    # 如果双引号前有终止符，那么双引号才是句子的终点，把分句符\n放到双引号后，注意前面的几句都小心保留了双引号
    para = para.rstrip()  # 段尾如果有多余的\n就去掉它
    # 很多规则中会考虑分号;，但是这里我把它忽略不计，破折号、英文双引号等同样忽略，需要的再做些简单调整即可。
    return para.split("\n")


def sentence_split(sentence, use_stopwords=True):
    """切分 sentence"""
    patten_other = re.compile(r'[^龘齯]+')
    sentence = re.sub(r'[龘齯﨡]+', '', sentence)
    patten_power = re.compile(r'[a-zA-Z0-9]*[\^_][0-9]+')  # n 次幂或 x_1
    powers = patten_power.findall(sentence)
    flags = patten_power.sub('龘', sentence)

    patten_degree = re.compile(r'[0-9]+\^?°')
    degrees = patten_degree.findall(flags)
    flags = patten_degree.sub('齯', flags)

    others = patten_other.findall(flags)
    flags = patten_other.sub('﨡', flags)

    split_sentence = []
    power_i, degree_i, other_i = 0, 0, 0
    for flag in flags:
        if flag == '龘':
            power_str = powers[power_i]
            split_sentence.append(power_str)
            power_i += 1
        elif flag == '齯':
            degree_str = degrees[degree_i]
            split_sentence.append(degree_str)
            degree_i += 1
        elif flag == '﨡':
            other_str = others[other_i]
            other_str = re.sub(r'[0-9]+', '数字', other_str)
            other_split = jieba.lcut(other_str)
            split_sentence.extend(other_split)
            other_i += 1
    if use_stopwords:
        sentence_lst = list()
        for word in split_sentence:
            if word not in stopwords:
                sentence_lst.append(word)
    else:
        sentence_lst = split_sentence
    return sentence_lst


def read_sentences(para):
    sent_list = cut_sent(para)
    for sent in sent_list:
        sentence = sentence_split(sent)
        yield sentence