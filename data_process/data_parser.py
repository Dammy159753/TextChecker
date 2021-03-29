# !/usr/bin/python3
# -*- coding:utf-8 -*-
# @Author : dyu
# @Time   : 2020-11-03
"""
Data Cleaner and Answer filled
"""
from data_processing import data_parser
from en_utils import _read_json, _write_json
import json
import argparse

def process(args):
    """
    填充答案数据整合
    :param grade_subject: 年级-科目, eg: senior_math
    :param gen_path :  源数据path
    :param save_path:  保存path
    :return:
    """
    new_data = dict()
    with open(args.gen_path, 'r', encoding='utf-8') as f :
        from tqdm import tqdm
        for line in tqdm(f.readlines()):
            data = dict()   # temp dict
            line = json.loads(line.strip())
            if isinstance(line, dict):
                if line['_id'] is not None:
                    data['question'] = line['question']
                    data['opts'] = line['opts']
                    data['labels'] = line['labels']
                    data['answers'] = line['answers']
                    data['difficulty'] = line['difficulty']
                    data['type'] = line['type']
                    new_data[line['_id']] = data

    print("数据大小为：", len(new_data))

    queries = data_parser.parse_data(args.grade_subject, new_data)   # 填充答案
    _write_json(queries, args.save_path)


if __name__ == "__main__":
    # process('senior_english',
    #         r'/media/chen2/Text_Quality_Inspection/en_data/ques_data_elite/高中英语_2020_1027.json',
    #         r'/media/chen2/Text_Quality_Inspection/en_data/filled_data/senior_english_20201102_filled.json')
    parser = argparse.ArgumentParser()
    parser.add_argument('--grade_subject',
                        help='Grade and sbject', required=True)
    parser.add_argument('--gen_path',
                        help='Source en_data path', required=True)
    parser.add_argument('--save_path',
                        help='Save en_data path', required=True)
    args = parser.parse_args()
    process(args)

