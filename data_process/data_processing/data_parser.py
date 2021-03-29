# !/usr/bin/python3
# -*- coding:utf-8 -*-
# @Author : licheng, dyu
# @Time   : 2020-05-22
"""
Data Cleaner and Answer filled
"""
from data_processing import deal_chemistry
from data_processing import deal_math
from data_processing import answer_filler

def parse_data(grade_subject, query_dct):
    """ Choose a different subject  """
    subject = grade_subject.split('_')[1]
    if subject in ['math', 'physics', 'biology', 'politics', 'geography']:
        return deal_math.clean_text(query_dct, labs=True)

    if 'chemistry' in grade_subject:
        return deal_chemistry.clean_text(query_dct)

    if 'history' in grade_subject:
        return answer_filler.data_process(query_dct, labs=True)

    if 'chinese' in grade_subject:
        return query_dct

    if 'english' in grade_subject:
        # return query_dct
        return answer_filler.data_process(query_dct, labs=True)


def process(grade_subject, gen_path, save_path):
    queries = parse_data(grade_subject, read_json(gen_path))
    save_json(json_data, save_path)
 
if __name__ == "__main__":
    process('senior_english', r'/media/chen2/Text_Quality_Inspection/en_data/ques_data_elite/高中英语_2020_1027.json', r'/media/chen2/Text_Quality_Inspection/en_data/filled_data/senior_english_20201102_filled.json')

