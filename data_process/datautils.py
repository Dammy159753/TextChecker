##################################################################################################
##                                    Data utils and tools                                      ##                                                                                             ##
##################################################################################################
# !/usr/bin/python3
# -*- coding:utf-8 -*-
# @Author : dengyu
# @Time   : 2019/11/20

import os
import codecs
from tqdm import tqdm
import json
import re
import warnings
warnings.filterwarnings("ignore")

def build_vocab():
    """ 构建词表 """
    dictionary = set()

    source_dic = list()
    stopwords = stopwordslist()
    with codecs.open(r'./dataset/train.txt', mode='r', encoding='utf-8') as fr:
        pbar = tqdm(fr.readlines())
        for line in pbar:
            line_list = line.strip().split(' ')	
            for word in line_list:
                if word in stopwords:
                    line_list.remove(word)
            #dictionary = dict()
            for i in line_list:
                source_dic.append(i)
            for word in line_list:
                dictionary.add(word)
            pbar.set_description("Processing:")
    dic = []
    dic_1 = []
    pattent = '^[’!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~●{}[]|%]+'
    for item in list(dictionary):
        if re.findall(r'^[^0-9.a-zA-z]+$', item) or re.findall(pattent, item):
            dic.append(item)
    print("正则后1：", len(dic))
    for item in dic:
        #if re.findall(r'^[_]+', item):
        if "_" in item: 
            pass
        else:
            dic_1.append(item)
    print("正则后2：", len(dic_1))
    with codecs.open(r'./dataset/w2idic.txt', mode='w', encoding="utf-8") as fw:
        #fw.write(json.dumps(dic, ensure_ascii=False))
        for word in dic_1:
            fw.write(word	 + '\n')


class SimSubjectTool:
    """ Find duplicate and similar en_data in the source en_data """
    def read_js(self, js_f):
        with open(js_f, 'r', encoding='utf8') as f:
            data = json.load(f)
        return data

    def save_js(self, data, save_f):
        with open(save_f, 'w', encoding='utf8') as f:
            json.dump(data,f, ensure_ascii=False)

    def cal_sim_tid(self, all_tid_dct_f, train_dct_f):
        sim_tid_dct = dict()
        all_tid_dct = self.read_js(all_tid_dct_f)
        train_dct = self.read_js(train_dct_f)
        for tid, train_item in tqdm(train_dct.items()):
            org_question = all_tid_dct[tid]['question']
            len_q = len(org_question)
            pos_tids = train_item["pos"]
            for pos_tid in pos_tids:
                sim_tid = []
                if pos_tid == tid:
                    continue
                pos_question = all_tid_dct[pos_tid]['question']
                distance = Levenshtein.distance(org_question, pos_question)
                ratio = 2 * distance / (len_q + len(pos_question))
                if ratio <= 0.1:
                    sim_tid.append([pos_tid, ratio])
            sim_tid_dct[tid] = sim_tid
        return sim_tid_dct

    def print_sim_tid(self):
        save_tid = []
        sim_tids = self.read_js('sim_tids.json')
        for tid, lst in sim_tids.items():
            if len(lst) > 0:
                print(lst)
                save_tid.append(lst)
        print(len(save_tid))

    def pipeline(self):
        sim_tids = self.cal_sim_tid('all_math_data_newest.json', 'all_processed_tid.json')
        self.save_js(sim_tids, 'sim_tids.json')
        self.print_sim_tid()


def stopwordslist():
    """停用词"""
    stopwords = [line.strip() for line in open('./dataset/stopword.txt', encoding='utf-8').readlines()]
    return stopwords

def find_error():
    w2i = dict()
    i = 1
    with codecs.open(r'./dataset/w2idic.txt', mode='r', encoding='utf-8') as fr:
        for line in fr.readlines():
            line = line.strip()
            w2i[line] = i
            i += 1
    with codecs.open(r'./dataset/w2idic.json', mode='w', encoding="utf-8") as fw:
        fw.write(json.dumps(w2i, ensure_ascii=False))


def _write_txt(path, data, batch=True):
    """
    write txt utils
    :paramter path: 
    :paramter dataset: 
    """
    if batch:
        with codecs.open(path, mode='w', encoding='utf-8') as fw:
            for item in data:
                fw.write(item + '\n')
    else:
        with codecs.open(path, mode='a', encoding='utf-8') as fw:
            fw.write(data + '\n')

def _write_json(dataset,store_path):
    """
    write json utils
    :paramter store_path:  store file path
    :paramter dataset: 
    """
    with codecs.open(store_path, mode='w', encoding='utf-8') as fw:
        fw.write(json.dumps(dataset, ensure_ascii=False))

def _read_json(path):
    """
    read json utils
    :paramter path: 
    """
    with codecs.open(path, mode='r', encoding='utf-8') as fr:
        read_data = json.load(fr)
    return read_data

def _judge_point_zero(string):
    """
    Judge point and zero if in string
    :paramter string :
    """
    if string.isdigit():
        if ".0" in string:
            return string[:-2]
        else:
            return string


def train_tid_trans(tid):
    """ 转换tid类型 """
    return str(int(float(tid)))

def elite_trans(elite):
    """ 转换elite值 """
    if elite is None:
        return -1
    return elite

if __name__ == '__main__':
    # find_error()
    pass
