# -*- coding: utf-8 -*-

# Copyright (c) 2019-present, AI
# All rights reserved.
# @Time 2019/10/18

# import logging
# logging.basicConfig(level = logging.INFO,format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename="gec.log")
# logger = logging.getLogger(__name__)
from nltk.tokenize import sent_tokenize, word_tokenize
from tqdm import tqdm
import time
# from gec_scripts.gec_postprocess import M2Filter
from GEC_check.gec_scripts.gec_postprocess import M2Filter
# from gec_scripts.location_convert import convert
from GEC_check.gec_scripts.location_convert import convert
# from config import config
from . import config
config = config.config
from flask import Flask, jsonify, request, make_response, abort
from fairseq import options
from . import GEC
GECModel = GEC.GECModel
from GEC_check.error_type import ERROR_TYPE_LIST
import re
import sys
from sys import path
# path.append("english_check")
from en_utils import spell_check_preprocess
from en_utils import NltkTool
import json
nt = NltkTool()
# import language_check
# tool = language_check.LanguageTool()
# tool.language = 'en'

# __version__ = '1.0'
# __all__ = ['GEC']

# app = Flask(__name__)
# app.config['JSON_AS_ASCII'] = True


def load_model():
    parser = options.get_generation_parser(interactive=True)
    args = options.parse_args_and_arch(parser)
    args_dict = vars(args)
    for key in config['gec_config']:
        args_dict[key] = config['gec_config'][key]
    gec = GECModel(args)
    filter = M2Filter(**config['post_process_config'])
    return gec, filter


def process(sentences_token):
    cor_sentences = gec.infer(sentences_token)
    # print("sentences_token",sentences_token)
    # print("cor_sentences",cor_sentences)
    result = []
    for ori, cor in zip(sentences_token, cor_sentences):
        golden_gec_edits, gec_edits, lt_edits = filter.process(ori, cor)
        result_dict = {}
        result_dict['ori'] = ori
        result_dict['golden_gec_edits'] = golden_gec_edits
        result_dict['gec_edits'] = gec_edits
        result_dict['lt_edits'] = lt_edits
        result.append(result_dict)
    return result


gec, filter = load_model()
print('load model completed!')

# 全局变量
GOLDEN_GEC_ID_TYPE = 'golden_gec'
GEC_ID_TYPE = 'gec'

def merge_gec_error_type(sub_error_type):
    for item in ERROR_TYPE_LIST:
        if sub_error_type in item['SUB']:
            return item['TYPE_CN']

def convert_gec_edit(edit, sentence_start_index, src_token, id_type):
    """

    :param edit: str type, for instance, A 12 13|||R:DET|||their|||REQUIRED|||-NONE-|||0
    :param sentence_start_index:
    :param src_token: a list of token
    :param id_type: str, gec or golden_gec
    :return:
    """
    # error_item = dict()
    msg = str()
    position, edit_type, modified_word, _, _, _ = edit.split('|||')
    position = position.split(' ')
    # start_pos = sentence_start_index + len(' '.join(src_token[0: int(position[1])]))
    start_pos = len(' '.join(src_token[0: int(position[1])]))
    # end_pos = sentence_start_index + len(' '.join(src_token[0: int(position[2])]))
    end_pos = len(' '.join(src_token[0: int(position[2])]))

    # error_item['rule'] = dict()
    # error_item['rule']['id'] = id_type
    # print('edit_type', edit_type)
    merge_type = merge_gec_error_type(edit_type[2:])
    # error_item['error_type'] = 'en_grammar_error'
    err_len = end_pos - start_pos if end_pos - start_pos > 0 else 0
    if start_pos == end_pos and modified_word != '':
        # error_item['description'] = '语法错误：' + merge_type + '，建议在' + src_token[int(position[1])-1] + '后面添加' + modified_word + '，位置[({},{})]'.format(start_pos + 1, start_pos + 1 + err_len)  # 插入
        msg = '语法错误：' + merge_type + '，建议在' + src_token[int(position[1])-1] + '后面添加' + modified_word  # 插入
    if end_pos > start_pos and modified_word == '':
        # error_item['description'] = '语法错误：' + merge_type + '，建议删除' + ' '.join(src_token[int(position[1]):int(position[2])]) + '，位置[({},{})]'.format(start_pos + 1, start_pos + 1 + err_len)  # 删除
        msg = '语法错误：' + merge_type + '，建议删除' + ' '.join(src_token[int(position[1]):int(position[2])])  # 删除
    if end_pos > start_pos and modified_word != '':
        # error_item['description'] = '语法错误：' + merge_type + '，建议将' + ' '.join(src_token[int(position[1]):int(position[2])]) + '替换为' + modified_word + '，位置[({},{})]'.format(start_pos + 1, start_pos + 1 + err_len)  # 替换
        msg = '语法错误：' + merge_type + '，建议将' + ' '.join(src_token[int(position[1]):int(position[2])]) + '替换为' + modified_word  # 替换
    # error_item['position'] = start_pos + 1
    # error_item['length'] = end_pos - start_pos if end_pos - start_pos > 0 else 0
    # assert error_item.get('description', 0) != 0
    return msg


def convert_lt_edit(edit, sentence_start_index):
    """

    :param edit:
    :return:
    """
    error_item = dict()
    error_item['offset_token'] = edit[3][0] + sentence_start_index
    error_item['length'] = edit[3][1]
    error_item['rule'] = dict()
    error_item['rule']['id'] = edit[0]
    error_item['rule']['category'] = edit[1]
    error_item['message'] = edit[2]
    return error_item


def standalone_test(post_content):
    start_pro = time.time()
    sentences = nt.sent_seg(post_content)
    # print('1',sentences)
    # sentences = [sent for sent in sentences if not re.search(r"[_]+",sent) and not tool.check(sent)] # 加了LT做第一步判断
    sentences = [sent for sent in sentences if not re.search(r"[_]+",sent)]
    # print('2',sentences)
    sentences_token = [' '.join(word_tokenize(sentence.strip())) for sentence in sentences]  # 注意此版本需自己分词
    results = process(sentences_token)
    # print("results",results)

    # tid_error_dict = dict()
    des_list = list()
    err_sents = list()
    sentence_start_index = 0

    # 重新对每个句子整理为字符级别offset-length格式, 消息形式
    for result_dict in results:
        # 针对每一个句子进行处理
        error_list = []
        # sent_error_dict = dict()
        src_token_list = result_dict['ori'].split(' ')  # todo: 是否有将一个句子多次分割之嫌
        golden_gec_edits = result_dict['golden_gec_edits']
        gec_edits = result_dict['gec_edits']
        # lt_edits = result_dict['lt_edits']

        for edit in golden_gec_edits:
            # error_item = convert_gec_edit(edit, sentence_start_index, src_token_list, GOLDEN_GEC_ID_TYPE)
            # error_list.append(error_item)
            msg = convert_gec_edit(edit, sentence_start_index, src_token_list, GOLDEN_GEC_ID_TYPE)
            error_list.append(msg)
        for edit in gec_edits:
            # error_item = convert_gec_edit(edit, sentence_start_index, src_token_list, GEC_ID_TYPE)
            # error_list.append(error_item)
            msg = convert_gec_edit(edit, sentence_start_index, src_token_list, GEC_ID_TYPE)
            error_list.append(msg)
        # if len(error_list) > 0:
        #     sent_error_dict['error_sent'] = result_dict['ori']
        #     sent_error_dict['error_detail'] = error_list
        #     all_error_list.append(sent_error_dict)
        if error_list:
            # print("des_list ", error_list)
            des_list.extend(error_list)
            err_sents.append(result_dict['ori'])
        sentence_start_index += len(result_dict['ori']) + 1

    return des_list, err_sents
        

        

    # if len(all_error_list) > 0:
    #     tid_error_dict[_tid] = all_error_list

    # end = time.time()
    # total = end - start_pro
    # print(total)
    # return all_error_list

if __name__ == '__main__':


    # 纯文本测试
    # content = "Which of the following dose not belong to a heat source?"

    # content = "Thanksgiving Day is special holiday in the United states and Canada Families and friends gather to eat and give thanks for their blessing Thanksgiving Day is really a harvest festival. This is why it is celebrated in late fall after the cops are in. But one of the first thanksgivings in America had nothing to do with a good harvest. On December 4 1619, the pilowins furm England God for the safe journey across the Aantic"
    # content = "I won't get hurt when I learn to cyclcng."
    content = "I'm just he a red of you are studying Chinese. And I am so proud of you had some progress of Chinese. I can give you some ad vices to love the study problems. And I have some questions need your ask, too.study Chinese is not difficult. In a nut shell, you can just listening and talking. You can also speak Chinese with your classmates to protect your spoken skills.For me, I can't understand the English reading in recently. Would you please tell me what should I do?Last, hope your things have work out. Best wishes for you. Li Hua"
    # content = spell_check_preprocess(content,rm_underline=False,rm_ch=True)
    # print(standalone_test(content))

    # 原题测试
    # test_data = r"/media/chen2/fxj/Text_Quality_Check_dev/english_check/test/test_data/writing_and_reading.json"
    test_data = sys.argv[1]
    save_file = r"/media/chen2/fxj/Text_Quality_Check_dev/english_check/test/test_out/202101/gec_all_grammar_error.json"
    time1 = time.time()
    # 全题库
    with open(test_data,'r',encoding='utf-8') as rf:
        lines = rf.readlines()
        error_tid = 0
        error_point = 0
        for line in tqdm(lines):
            tid_dict = json.loads(line)
            tid_type = tid_dict["type"]
            _id = tid_dict["_id"]
            if tid_type == "书面表达":
                tid_error_dict = dict()
                answer = tid_dict['answers']
                if len(answer) == 1 and isinstance(answer[0],str):
                    text = spell_check_preprocess(answer[0],rm_underline=False,rm_ch=True)
                    tid_error_list = standalone_test(text)
                    if len(tid_error_list) > 0:
                        tid_error_dict[_id] = tid_error_list
                        error_point += len(list(tid_error_dict.values())[0])
                        with open(save_file,'a',encoding='utf-8') as af:
                            error_str = json.dumps(tid_error_dict, ensure_ascii=False)
                            af.write(error_str+"\n")
            elif tid_type == "阅读理解":
                question = tid_dict['question']
                if isinstance(question,str):
                    text = spell_check_preprocess(question,rm_underline=False,rm_ch=True)
                    tid_error_list = standalone_test(text)
                    if len(tid_error_list) > 0:
                        tid_error_dict[_id] = tid_error_list
                        error_point += len(list(tid_error_dict.values())[0])
                        with open(save_file,'a',encoding='utf-8') as af:
                            error_str = json.dumps(tid_error_dict, ensure_ascii=False)
                            af.write(error_str+"\n")
            else:
                continue    
        print("Finish grammar check. {} error queries with {} error point found in total {} queries.".format(error_tid,error_point,len(lines)))


# {"_id": 1638508287, "question": "Eight days for just ¥12,000Departs: May, October 2017Includes:•Return flights from 6 China's airports to Naples•Return airport to hotel transport•Seven nights' accommodation at the 3-star Hotel Nice•Breakfast•The service of guides•Government taxesJoin us for a wonderful holiday in one of the Europe's most wonderful corners—Naples in Italy if you want to have a nice time in a beautiful small quiet place. The ancient Romans called the city \"happy land\" with attractive coastline, colorful towns, splendid views and the warm Mediterranean Sea. Your best choice for a truly memorable holiday!Choose between the peaceful traditional villages of Sant' Agata, set on a hillside six miles away from Sorrento, or the more lively and well-known international resort town of Sorrento, with wonderful views over the Bay of Naples.Breathtaking scenery, famous sights and European restaurants everywhere. From the mysterious Isle of Capri to the hunting ruins of Pompeii, and from the unforgettable \"Amalfi Drive\" to the delightful resorts of Positano, Sorrento and Ravello, the area is a feast for the eyes! Join us and you won't be disappointed!Price based on two tourists sharing a double room at the Hotel Nice. A single room, another ¥ 2,000. A group of ten college students, ¥ 10,000 for each.Like to know more? Telephone Newmarket Air Holidays Ltd. on: 0845-226-7788 (All calls charged at local rates).\t（1）All the following are included in the price of ¥12,000 EXCEPT ______.\t（2）If you like to visit historical sites, which of the following is your best choice?\t（3）If you don't like sharing a room with others, you have to pay ______.\t（4）Who is the advertisement intended for?", "opts": [{"A": "transport between the airport and the hotel", "B": "telephone calls made by tourists", "C": "the service of guides to tourists", "D": "double rooms for every two tourists"}, {"A": "Amalfi.", "B": "Sant' Agata.", "C": "Pompeii.", "D": "Sorrento."}, {"A": "¥12,000", "B": "¥10,000", "C": "¥2,000", "D": "¥14,000"}, {"A": "Potential tourists.", "B": "College students.", "C": "Quiet people.", "D": "Old people."}], "labels": ["推理判断", "应用文阅读", "细节理解", "广告布告类阅读"], "answers": ["B", "C", "D", "A"], "solutions": ["（1）B 细节理解题。根据文章开始部分提到的12000元的费用包括项目以及文章最后提到打电话的费用All calls charged at local rates，可知电话费用不包括在内，按当地费用收费。故选B。", "（2）C 细节理解题。根据文章Breathtaking scenery, famous sights and European restaurants everywhere. From the mysterious Isle of Capri to the hunting ruins of Pompeii可知，如果你喜欢参观名胜古迹应该选择 Pompeii。故选C。", "（3）D 细节理解题。根据倒数第二段A single room, another¥2,000。可知，如果住单间，要另交2000元费用，所以总共要付14000元。故选D。", "（4）A 推理判断题。根据最后一段Like to know more? Telephone Newmarket Air Holidays Ltd. on: 0845-226-7788 (All calls charged at local rates) 可知广告是为了吸引潜在的顾客去旅游。故选A。"], "explanations": ["本文是一篇旅游宣传，吸引人们到意大利的Naples（那不勒斯）去旅游。", "", "", ""], "difficulty": 0.4, "type": "阅读理解"}
