#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time   : 2020/11/11 - 15:57
# @Modify : 2020/11/11 - 15:57
# @Author : dyu
# @File : subject_analyze.py
# @Function :

import os
import re
import json
from tqdm import tqdm
from collections import OrderedDict, Counter
from utils_old import getnestList

def collect_type():
    """
    收集题型
    :return:
    """
    gen_path = r'/media/chen2/Text_Quality_Inspection/en_data/ques_data_elite'
    for every_json in os.listdir(gen_path):
        domain = os.path.abspath(gen_path)
        json_path = os.path.join(domain, every_json)
        subject_name = every_json[:4]
        print(subject_name)
        all_type = list()
        with open(json_path, 'r', encoding='utf-8') as f :
            for line in f.readlines():
                line = eval(line.strip())
                all_type.append(line['type'])
        print("Type:", set(all_type))
        print("Nums:", dict(Counter(all_type)))
        print('-' * 100)


def pull_trouble_data():
    """
    某学科中有问题的题型，提取反馈给老师
    :return:
    """
    trouble_subject = {"初中语文":["解答题", "写作题"],
                       "初中英语":"解答题",
                       "高中英语":"解答题",
                       "高中化学":"实验探究题",
                       "初中政治":"解答题",
                       "高中政治":"解答题",
                       "初中历史":"解答题",
                       "高中历史":"解答题"}

    gen_path = r'/media/chen2/Text_Quality_Inspection/en_data/ques_data_20201111'

    with open(r'./subject_error_id.txt', 'a', encoding='utf-8') as fw:
        for every_json in os.listdir(gen_path):
            domain = os.path.abspath(gen_path)
            json_path = os.path.join(domain, every_json)
            subject_name = every_json[:4]
            if subject_name in trouble_subject.keys():
                error_type = trouble_subject[subject_name]
                # print(error_type)
                error_id = []
                if isinstance(error_type, list):
                    for _type in error_type:
                        sub_error_id = []
                        fw.write(subject_name + '-' + _type)
                        fw.write('\n')
                        with open(json_path, 'r', encoding='utf-8') as f:
                            for line in tqdm(f.readlines()):
                                line = eval(line.strip())
                                if line['type'] == _type:
                                    sub_error_id.append(line['_id'])
                        fw.write(str(sub_error_id))
                        fw.write('\n')
                else:
                    print(subject_name + '-' + error_type)
                    fw.write(subject_name + '-' + error_type)
                    fw.write('\n')
                    with open(json_path, 'r', encoding='utf-8') as f:
                        for line in tqdm(f.readlines()):
                            line = eval(line.strip())
                            if line['type'] == error_type:
                                error_id.append(line['_id'])
                    print(error_id)
                    fw.write(str(error_id))
                    fw.write('\n')
                fw.write("-" * 100)
                fw.write('\n')

def sub_type_analyse():
    """
    不同体型包含的小题
    :return:
    """
    all_type = []
    type_set = []
    partly_type_set = []
    no_type_set = []
    error_type_set_1 = []
    error_type_set_2 = []

    gen_path = r'/media/chen2/Text_Quality_Inspection/en_data/ques_data_20201111/'

    p1 = re.compile(r'[（\(]\d+[）\)]')

    special_answers = []

    for every_json in os.listdir(gen_path):
        domain = os.path.abspath(gen_path)
        json_path = os.path.join(domain, every_json)
        m = 0
        if every_json[:4] == '高中物理':
            with open(json_path, 'r', encoding='utf-8') as f :
                for line in f.readlines():
                    line = eval(line.strip())
                    all_type.append(line['type'])
                    if len(re.findall(p1, line['question'])) != 0 and len(re.findall(p1, getnestList(line['answers'], True))) != 0 and len(re.findall(p1, ''.join(line['solutions'][0]))) != 0:
                        type_set.append(line['type'])
                    elif len(re.findall(p1, line['question'])) != 0:
                        if len(re.findall(p1, getnestList(line['answers'], True))) != 0 or len(re.findall(p1, ''.join(line['solutions'][0]))) != 0:
                            partly_type_set.append(line['type'])
                        else:
                            error_type_set_1.append(line['type'])
                        # if len(re.findall(p1, getnestList(line['answers'], True) ) ) == 0 :
                        #     if line['type'] not in ["填空题","选择题","作图题"]:
                        #         print("1:", line)
                        #         special_answers.append(line['answers'])
                        #         m += 1
                    elif len(re.findall(p1, line['question'])) == 0:
                        if len(re.findall(p1, getnestList(line['answers'], True) )) != 0 and len(re.findall(p1, ''.join(line['solutions'][0]))) == 0:
                            if line['type'] != '判断题':
                                error_type_set_2.append(line['type'])
                            # pass
                        else:
                            no_type_set.append(line['type'])
                    else:
                        no_type_set.append(line['type'])
            print(m)
            print("--------------------------------------------------------------------")
            print("(1)科目           :", every_json[:4])
            print("(2)所有题型       :", sorted(dict(Counter(all_type)).items(), key=lambda x:x[0], reverse=False))
            print("(3)全部含有小题题型:", sorted(dict(Counter(type_set)).items(), key=lambda x:x[0], reverse=False))
            print("(4)部分含有小题题型:", sorted(dict(Counter(partly_type_set)).items(), key=lambda x:x[0], reverse=False))
            print("(5)Q1_A/S0题型错误:", sorted(dict(Counter(error_type_set_1)).items(), key=lambda x: x[0], reverse=False))
            print("(6)Q0_A/S1题型错误:", sorted(dict(Counter(error_type_set_2)).items(), key=lambda x: x[0], reverse=False))
            print("(7)不含有小题题型  :", sorted(dict(Counter(no_type_set)).items(), key=lambda x:x[0], reverse=False))
            print("--------------------------------------------------------------------" + '\n')

            print(dict(Counter(getnestList(special_answers))))

if __name__ == "__main__":
    # pull_trouble_data()

    sub_type_analyse()


