#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# @File    :   en_utils.py
# @Time    :   2020/11/12
# @Author  :   dyu

import os
import re
import nltk
from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters
import spacy
from nltk.tokenize import MWETokenizer
import json
import enchant
import numpy as np
from logserver import log_server
from collections import Counter
# from autocorrect import Speller
from enchant.checker import SpellChecker
# from tagger_master.model import Model
# from tagger_master.utils import create_input, iobes_iob, iob_ranges, zero_digits
# from tagger_master.loader import prepare_sentence
from sequence_tagging_master.model.data_utils import CoNLLDataset
from sequence_tagging_master.model.ner_model import NERModel
from sequence_tagging_master.model.config import Config
import Levenshtein

def parse_data(query):
    """
    解析数据
    """
    # tid = str(list(query.values())[0]["_id"])
    # _type = list(query.values())[0]['type']
    # question = list(query.values())[0]['description']
    # answers = list(query.values())[0]['answers']
    # stems = list(query.values())[0]['stems']
    # solutions = list(query.values())[0]['solutions']
    tid = query["_id"]
    _type = query["type"]
    question = query['description']
    answers = query["answers"]
    stems = query["stems"]
    solutions = query["solutions"]
    return tid, question, answers, stems, solutions, _type


def write_to_txt(data,file):
    """Saving en_data to txt file"""
    with open(file,'a') as af:
        af.write(data)
        af.write('\n\n')


def is_Chinese(word):
    """Jugde whether a word is in Chinese"""
    for ch in word:
        if '\u4e00' <= ch <= '\u9fff':
            return True
    return False


def rm_point_zero(num_list):
    """Remove point zero in a number string or a number list"""
    if isinstance(num_list, list):
        new_list = []
        for i in num_list:
            i = str(i)
            if '.0' in i:
                i = i[:-2]
            new_list.append(i)
        return new_list
    else:
        num = str(num_list)
        if '.0' in num:
            num = num[:-2]
        return num

def write_to_json(dataset,store_path):
    """write json utils"""
    with open(store_path, mode='w', encoding='utf-8') as fw:
        fw.write(json.dumps(dataset, ensure_ascii=False, indent=4, separators=(',', ':')))
        # fw.write(json.dumps(dataset, ensure_ascii=False))

def read_json(data_path):
    with open(data_path,'r',encoding='utf-8') as rf:
        data_dict = json.load(rf)
    return data_dict

def get_dict_list(dict_path):
    """Transform a word dictionary to a word list"""
    dict_list = [line.strip() for line in open(dict_path,'r',encoding='utf-8')]
    return dict_list

# 2021/2/18 modified
def spell_check_preprocess(text,rm_num=True,rm_special=True,rm_underline=True,sub_ch=True,add_space=True,rm_num_sym=True,rm_ch=False):
    """This method is suitable for spelling check"""
    if rm_num == True:
        # text= re.sub(r'[\d]+[.]|[（|(][\d]+[)|）]|[①②③④⑤⑥⑦⑧⑨]','',text)
        text= re.sub(r'[（|(][\d]+[)|）]|[①②③④⑤⑥⑦⑧⑨]',' ',text)
    if rm_special == True:
        text = re.sub(r"[\n【】●◆•★☆✯♦◇→\*▲＄\$▶▷■=◎◉·+※＞©®▪□＋™+]", ' ', text)
        text = re.sub('\xa0|\t|\xad', ' ', text)
        # text = re.sub('[_]+',' ',text)
        # text = re.sub('[—]+',' ',text)
        text = re.sub(r'\(|\)|（|）|\\|\/',' ',text)
    if rm_underline == True:
        text = re.sub('[_]+|[—]+', ' ', text)
    if sub_ch == True:
        text = re.sub(r'。','.',text)
        text = re.sub(r'？','?',text)
        text = re.sub(r'！','!',text)
        text = re.sub(r'；',';',text)
        text = re.sub(r'．','.',text)
        # text = re.sub(r'·','.',text)
        text = re.sub(r'、',', ',text)
        text = re.sub(r'，',',',text)
        text = re.sub(r"``","\"",text)
        text = re.sub(r"\'\'","\"",text)
        text = re.sub(r"＠",'@',text)
        text = re.sub(r"[−﹣]","-",text)
    
    if add_space == True:
        text = re.sub(r'(.?[\.])([A-Z])', r'\1 \2', text)
        # text = re.sub(r'\?','? ',text)
        text = re.sub(r'(.?[\?])([a-zA-Z])', r'\1 \2', text)
        # text = re.sub(r'!','! ',text)
        text = re.sub(r'(.?[!])([a-zA-Z])', r'\1 \2', text)
    
    if rm_num_sym == True:
        # 数字形式符号编码集
        text = re.sub(r'[\u2150-\u218F]',' ',text)

    if rm_ch == True:
        # 去除汉字
        text = re.sub(r"[\u4e00-\u9fa5]+",'',text)
  
    return text

def get_recursively_list(list_name):
    '''
    Process recursively list
    递归处理嵌套列表找出最小元素
    '''
    processed_list = []
    def Recursively_List(list_name):
        for i in list_name:
            if isinstance(i,list):
                Recursively_List(i)
            else:
                processed_list.append(i)
    Recursively_List(list_name)
    return processed_list

def get_answers(answer_list):
    new_ans_list = list()
    if isinstance(answer_list,list):
        if len(answer_list) > 1:
            for ans in answer_list:
                if isinstance(ans,list) and len(ans) == 1:
                    new_ans_list.append(ans[0])
                elif isinstance(ans,list) and len(ans) > 1:
                    new_ans_list.append(ans)
                elif isinstance(ans, str):
                    new_ans_list.append(ans)
        elif isinstance(answer_list[0],str):
            new_ans_list.append(answer_list[0])
        elif isinstance(answer_list[0], list):
            new_ans_list.extend(answer_list[0])
    return new_ans_list

def get_recursively_word_split(word):
    """切分连在一起的多个单词（以大写切分）"""
    sub_word = list()
    def recursively_word_split(start_index, word):
        if start_index != len(word)-1:
            res = re.search(r'[A-Z]', word[start_index+1:])
            if res:
                index = res.span()[1]
                sub_word.append(word[start_index:index])
                word = word[index:]
                recursively_word_split(0, word)
            else:
                sub_word.append(word)
                return sub_word
        else:
            sub_word.append(word)
            return sub_word
    recursively_word_split(0, word)
    return sub_word

# 12.25修改代码
def trans_cy(word):
    """西里尔字母转换"""
    with open(r"english_check/en_data/Cyrillic_map.json",'r',encoding='utf-8') as rf:
        cy_map = rf.read()
        cy_dict = json.loads(cy_map)
        cy_code = list(cy_dict.keys())
        alph_list = list(word)
        for index,a in enumerate(alph_list):
            if a in cy_code:
                # print('origin code',a.encode('unicode_escape'))
                alph_list[index] = cy_dict[a]
                # print('trans code',alph_list[index].encode('unicode_escape'))
        word = ''.join(alph_list)
    return word

# 12.25修改代码
# def filt_word(word_list):
#     """用于拼写检查预处理阶段：过滤不做拼写检查的单词"""
#     # 过滤带@的邮箱地址
#     token_dict = dict(Counter(word_list))
#     # print("token_dict",token_dict)
#     if '@' in token_dict.keys():
#         symbol_num = token_dict['@']
#         for i in range(symbol_num):
#             if "@" in word_list:
#                 symbol_index = word_list.index('@')
#                 j = 0
#                 while j < 3:
#                     word_list.pop(symbol_index - 1)
#                     j += 1
#     filt_word_list = list()
#     for word in word_list:
#         word = trans_cy(word)
#         res1 = re.search(r"[\u4e00-\u9fa5\d]+", word) # 汉字数字
#         res2 = re.search(r"\.com|\.org|www\.|\.cn|\.edu|\.uk", word) # 网址关键字
#         res3 = re.search(r"[ʃɪæəʊɔʌ£ːɒɑüéθŋʈɖɓɗɱɳɸβðʒʂʐɛɐכ]",word) # 音标字符
#         res4 = re.search(r"[a-zA-Z]+",word)
#         if not (res1 or res2 or res3) and res4:
#             filt_word_list.append(word)
#     return filt_word_list

# 2021/2/18 modified
def filt_word(word_list):
    """用于拼写检查预处理阶段：过滤不做拼写检查的单词（新）"""
    # 尝试只检查没有其他符号的单词
    # 过滤带@的邮箱地址
    token_dict = dict(Counter(word_list))
    if '@' in token_dict.keys():
        symbol_num = token_dict['@']
        for i in range(symbol_num):
            if "@" in word_list:
                symbol_index = word_list.index('@')
                j = 0
                while j < 3:
                    word_list.pop(symbol_index - 1)
                    j += 1
    filt_word_list = list()
    for word in word_list:
        word = trans_cy(word)
        if not re.search(r"[^a-z^A-Z^\-^']",word):
            filt_word_list.append(word)
    return filt_word_list

def get_common_str(str1, str2):
    '''
    Obtain the maximum common string between two strings
    获取两个字符串的最大公共子字符串的长度
    '''
    lstr1 = len(str1)
    lstr2 = len(str2)
    record = [[0 for i in range(lstr2 + 1)] for j in range(lstr1 + 1)]  # 多一位
    maxNum = 0  # 最长匹配长度
    # p = 0  # 匹配的起始位
    for i in range(lstr1):
        for j in range(lstr2):
            if str1[i] == str2[j]:
                # 相同则累加
                record[i + 1][j + 1] = record[i][j] + 1
                if record[i + 1][j + 1] > maxNum:
                    # 获取最大匹配长度
                    maxNum = record[i + 1][j + 1]
                    # 记录最大匹配长度的终止位置
                    # p = i + 1
    return maxNum

def order_list(input_list):
    """对返回的error list[{},{},...]加序号key"""
    output_list = list()
    for i, item in enumerate(input_list):
        item["_id"] = i + 1
        output_list.append(item)
    return output_list

def make_dict(des, source, target, pos, _type, replace):
    """返回error detail字典"""
    error_detail = dict()
    # error_detail["_id"] = _id
    error_detail["description"] = des
    error_detail["source"] = source
    error_detail["target"] = target
    error_detail["position"] = pos
    error_detail["error_type"] = _type
    error_detail["replace"] = replace
    return error_detail

def merge_dicts(tid, *err_dicts):
    """融合多个返回的错误字典"""
    all_error_dict = dict()
    for err_dict in err_dicts:
        if err_dict:
            if not all_error_dict:
                all_error_dict = err_dict
            else:
                temp_error_list = list(err_dict.values())[0]
                exist_error_list = list(all_error_dict.values())[0]
                for i in range(len(temp_error_list)):
                    for j in range(len(exist_error_list)):
                        if temp_error_list[i]["error_sent"] == exist_error_list[j]["error_sent"]:
                            exist_error_list[j]["error_detail"].extend(temp_error_list[i]["error_detail"])
                            break
                        else:
                            if j == len(exist_error_list) - 1:
                                exist_error_list.extend(temp_error_list)
                            else:
                                continue
                all_error_dict[tid] = exist_error_list
        else:
            continue
    if all_error_dict:
        for i in range(len(list(all_error_dict.values())[0])):
            all_error_dict[tid][i]["error_detail"] = order_list(all_error_dict[tid][i]["error_detail"])
    return all_error_dict
    

# 2021/2/18 modified 融合了所有格式检查子功能
class FormatChecker():
    """检查符号使用格式的功能类"""
    def __init__(self):
        self.nt = NltkTool()

    def bracket(self,text):
        '''
        name: 括号检测
        msg: 检测括号符号是否匹配
        param: text-输入文本
        return: flag={TRUE，FALSE}-是否匹配
                stack
        '''
        BRANKETS = {'}':'{',
                ']':'[',
                ')':'(',
                '”':'“',
                '’':'‘',
                '）':'（',
                '】':'【',
                '>':'<',
                '》':'《'}
        BRANKETS_LEFT, BRANKETS_RIGHT = BRANKETS.values(), BRANKETS.keys()
        stack = []
        for i,char in enumerate(text):
            # 如果是左括号
            if char in BRANKETS_LEFT:
                # 入栈
                stack.append((char,i))
            # 右括号
            elif char in BRANKETS_RIGHT:
                # stack不为空，并且括号匹配成功
                if stack and stack[-1][0] == BRANKETS[char]:
                    # 出栈
                    stack.pop()
                # 匹配成功
                else:
                    return False,stack
                    # return stack
        return not stack, stack
        # return stack

    def bracket_checker(self,text):
        '''
        name: 括号检查入口
        msg: 
        param: text
        return: bracket_error_list
        '''
        # stop_syms = '，。！？；,.!?;'
        flag,stack = self.bracket(text)
        # bracket_error_list = list()
        error_pos = list()
        ori_list = list()
        if flag == False:
            for stk in stack:
                # sent_error_dict = dict()
                # error_detail_dict = dict()
                char = stk[0]
                start_index = stk[1]
                end_index = start_index + len(char)
                error_pos.append((start_index, end_index))
                ori_list.append(char)
        return error_pos, ori_list

    def check_full_width(self,text):
        '''
        name: 全半角混用检查器
        msg: 
        param: text
        return: full_width_error_list
        '''
        # error_detail_list = list()
        # error_detail_dict = dict()
        # fw_alphabet = ['Ａ','Ｂ','Ｃ','Ｄ','Ｅ','Ｆ','Ｇ','Ｈ','Ｉ','Ｊ','Ｋ','Ｌ','Ｍ','Ｎ','Ｏ','Ｐ','Ｑ','Ｒ','Ｓ','Ｔ','Ｕ','Ｖ','Ｗ','Ｘ','Ｙ','Ｚ']
        fw_map = {'Ａ':'A',
                  'Ｂ':'B',
                  'Ｃ':'C',
                  'Ｄ':'D',
                  'Ｅ':'E',
                  'Ｆ':'F',
                  'Ｇ':'G',
                  'Ｈ':'H',
                  'Ｉ':'I',
                  'Ｊ':'J',
                  'Ｋ':'K',
                  'Ｌ':'L',
                  'Ｍ':'M',
                  'Ｎ':'N',
                  'Ｏ':'O',
                  'Ｐ':'P',
                  'Ｑ':'Q',
                  'Ｒ':'R',
                  'Ｓ':'S',
                  'Ｔ':'T',
                  'Ｕ':'U',
                  'Ｖ':'V',
                  'Ｗ':'W',
                  'Ｘ':'X',
                  'Ｙ':'Y',
                  'Ｚ':'Z',
                  'ａ':'a',
                  'ｂ':'b',
                  'ｃ':'c',
                  'ｄ':'d',
                  'ｅ':'e',
                  'ｆ':'f',
                  'ｇ':'g',
                  'ｈ':'h',
                  'ｉ':'i',
                  'ｊ':'j',
                  'ｋ':'k',
                  'ｌ':'l',
                  'ｍ':'m',
                  'ｎ':'n',
                  'ｏ':'o',
                  'ｐ':'p',
                  'ｑ':'q',
                  'ｒ':'r',
                  'ｓ':'s',
                  'ｔ':'t',
                  'ｕ':'u',
                  'ｖ':'v',
                  'ｗ':'w',
                  'ｘ':'x',
                  'ｙ':'y',
                  'ｚ':'z'}
        # 先判断是否存在混用情况
        # stop_syms = '，。！？；,.!?;'
        # full_width_error_list = list()
        full_alphabet = list(fw_map.keys())
        error_pos = list()
        ori_apb = list()
        cor_apb = list()
        if re.search(r'[a-zA-Z]',text) and re.search(r'[{}]'.format(''.join(full_alphabet)),text):
            # 存在混用，确定错误位置
            for i,char in enumerate(text):
                if char in full_alphabet:
                    cor_text = list(text)
                    cor_text[i] = fw_map[char]
                    cor_text = ''.join(cor_text)
                    # error_detail_dict = dict()
                    error_pos.append((i,i+1))
                    ori_apb.append(text[i:i+1])
                    cor_apb.append(fw_map[char])
        return error_pos, ori_apb, cor_apb

    def ch_punc_check(self, text):
        '''
        name: 中英文符号检查器
        msg: 检查中英文符号使用错误
        param: sent
        return: punc_error_list
        '''
        # sent_error_dict = dict()
        # sent_error_dict["error sent"] = sent
        # punc_error_list = list()
        symbol_map = {"，":",","。":".","？":"?","‘":"\'","’":"'","“":"\"","”":"\"","：":":"}
        ch_sym = list(symbol_map.keys())
        sents = self.nt.sent_seg(text)
        error_sents = list()
        ori_text = list()
        cor_text = list()
        for sent in sents:
            if not re.search(r"[\u4e00-\u9fa5]+", sent): # 句子里没有中文字符，则不能出现中文符号
                # 先判断是否存在中文符号
                if re.search(r"[{}]".format(''.join(ch_sym)),sent):
                    # 确定位置
                    for char in sent:
                        if char in ch_sym:
                            ori_text.append(char)
                            cor_text.append(symbol_map[char])
                            error_sents.append(sent)
                        else:
                            continue
                else:
                    continue
            else:
                continue
        return error_sents, ori_text, cor_text
                    
    def web_format_check(self, text):
        """网址格式检查"""
        '''
        name: 网址格式检查
        msg: 暂时只针对www.格式检查
        param: sent
        return: error_detail_list
        '''
        # error_detail_list = list()
        start_index = 0
        error_pos = list()
        ori_text = list()
        cor_text = list()
        while re.search(r"www", text):
            start_index = re.search("www",text).span()[0] # www起始位置
            temp_index = re.search("www", text).span()[1]  # www结束位置
            # log_server.logging("sent"+sent[temp_index:temp_index+10])
            err = re.search(r"^[\.][ ]+[a-zA-Z0-9]|^[ ]+[\.][ ]*[a-zA-Z0-9]", text[temp_index:])
            # print(err)
            if err:
                err_len = err.span()[1] - err.span()[0] - 1
                end_index = start_index + 3 + err_len
                error_pos.append((start_index, end_index))
                ori_text.append(text[start_index:end_index])
                cor_text.append("www.")
            text = text[temp_index:]
        return error_pos, ori_text, cor_text


    def format_checker(self,query):
        """格式检查器入口"""
        tid, question, answers, stems, solutions, _ = parse_data(query)
        format_error_dict = dict()
        tid_error_list = list()
        # 检查description
        ques_error_dict = dict()
        ques_detail_list = list()
        error_pos, ori_list = self.bracket_checker(str(question)) # 检查括号匹配
        if error_pos: 
            des = "大题干文本存在括号/引号不匹配，错误位置：{}，对应错误符号：{}".format(error_pos, ori_list)
            source = None
            target = None
            pos = None
            _type = "括号/引号不匹配错误"
            replace = 0
            q_bracket = make_dict(des, source, target, pos, _type, replace)
            ques_detail_list.append(q_bracket)
        error_pos, ori_text, cor_text = self.check_full_width(str(question)) # 检查全半角
        if error_pos: 
            des = "大题干文本存在全半角英文字符混用"
            source = ori_text
            target = cor_text
            pos = error_pos
            _type = "全半角字符混用错误"
            replace = 1
            q_full_width = make_dict(des, source, target, pos, _type, replace)
            ques_detail_list.append(q_full_width)
        error_pos, ori_text, cor_text = self.web_format_check(str(question)) # 检查网址
        if error_pos:
            des = "大题干文本存在网址格式错误"
            source = ori_text
            target = cor_text
            pos = error_pos
            _type = "网址格式错误"
            replace = 1
            q_web = make_dict(des, source, target, pos, _type, replace)
            ques_detail_list.append(q_web)
        error_sents, ori_text, cor_text = self.ch_punc_check(str(question))
        if error_sents:
            des = "大题干文本存在中英文符号混用，错误符号：{}，建议修改：{}，错误句子：{}".format(ori_text, cor_text, error_sents)
            source = None
            target = None
            pos = None
            _type = "中英文符号混用错误"
            replace = 0
            q_punc = make_dict(des, source, target, pos, _type, replace)
            ques_detail_list.append(q_punc)
        # 题目错误汇总
        if ques_detail_list:
            # ques_detail_list = order_list(ques_detail_list)
            ques_error_dict["error_sent"] = "description"
            ques_error_dict["error_detail"] = ques_detail_list
            tid_error_list.append(ques_error_dict)

        # 检查小题干
        if stems:
            stems_error_dict = dict()
            stems_detail_list = list()
            brac_error_pos = list() # 存括号检查结果
            brac_ori_list = list()
            fw_error_pos = list() # 存全半角检查结果
            fw_ori_list = list()
            fw_cor_list = list()
            web_error_pos = list() # 存网址检查结果
            web_ori_list = list()
            web_cor_list = list()
            punc_error_sents = list() # 存中英文符号检查结果
            punc_ori_list = list()
            punc_cor_list = list()
            for i, stem_dict in enumerate(stems):
                error_pos_1, ori_list_1 = self.bracket_checker(str(stem_dict["stem"])) # 检查括号匹配
                if error_pos_1:
                    for pos in error_pos_1:
                        brac_error_pos.append((i, pos))
                    brac_ori_list.extend(ori_list_1)
                error_pos_2, ori_text_2, cor_text_2 = self.check_full_width(str(stem_dict["stem"]))
                if error_pos_2:
                    for pos in error_pos_2:
                        fw_error_pos.append((i, pos))
                    fw_ori_list.extend(ori_text_2)
                    fw_cor_list.extend(cor_text_2)
                error_pos_3, ori_text_3, cor_text_3 = self.web_format_check(str(stem_dict["stem"]))
                if error_pos_3:
                    for pos in error_pos_3:
                        web_error_pos.append((i,pos))
                    web_ori_list.extend(ori_text_3)
                    web_cor_list.extend(cor_text_3)
                error_sents_4, ori_text_4, cor_text_4 = self.ch_punc_check(str(stem_dict["stem"]))
                if error_sents_4:
                    punc_error_sents.extend(error_sents_4)
                    punc_ori_list.extend(ori_text_4)
                    punc_cor_list.extend(cor_text_4)
            if brac_error_pos:
                des = "小题干文本存在括号/引号不匹配，错误位置：{}，对应错误符号：{}".format(brac_error_pos, brac_ori_list)
                source = None
                target = None
                pos = None
                _type = "括号/引号不匹配错误"
                replace = 0
                stems_brac = make_dict(des, source, target, pos, _type, replace)
                stems_detail_list.append(stems_brac)
            if fw_error_pos:
                des = "小题干文本存在全半角英文字符混用"
                source = fw_ori_list
                target = fw_cor_list
                pos = fw_error_pos
                _type = "全半角字符混用错误"
                replace = 1
                stems_fw = make_dict(des, source, target, pos, _type, replace)
                stems_detail_list.append(stems_fw)
            if web_error_pos:
                des = "小题干文本存在网址格式错误"
                source = web_ori_list
                target = web_cor_list
                pos = web_error_pos
                _type = "网址格式错误"
                replace = 1
                stems_web = make_dict(des, source, target, pos, _type, replace)
                stems_detail_list.append(stems_web)
            if punc_error_sents:
                des = "小题干文本存在中英文符号混用，错误符号：{}，建议修改：{}，错误句子：{}".format(punc_ori_list, punc_cor_list, punc_error_sents)
                source = None
                target = None
                pos = None
                _type = "中英文符号混用错误"
                replace = 0
                stems_punc = make_dict(des, source, target, pos, _type, replace)
                stems_detail_list.append(stems_punc)
            # 答案错误汇总
            if stems_detail_list:
                # stems_detail_list = order_list(stems_detail_list)
                stems_error_dict["error_sent"] = "stems"
                stems_error_dict["error_detail"] = stems_detail_list
                tid_error_list.append(stems_error_dict)

        # 检查答案
        ans_error_dict = dict()
        ans_detail_list = list()
        if not answers: # 检查答案为空
            des= "答案为空"
            source = None
            target = None
            pos = None
            _type = "答案为空错误"
            replace = 0
            ans_null = make_dict(des, source, target, pos, _type, replace)
            ans_detail_list.append(ans_null)
        else:
            answers = get_recursively_list(answers)
            brac_error_pos = list() # 存括号检查结果
            brac_ori_list = list()
            fw_error_pos = list() # 存全半角检查结果
            fw_ori_list = list()
            fw_cor_list = list()
            web_error_pos = list() # 存网址检查结果
            web_ori_list = list()
            web_cor_list = list()
            punc_error_sents = list() # 存中英文符号检查结果
            punc_ori_list = list()
            punc_cor_list = list()
            for i, ans in enumerate(answers): # 检查括号
                error_pos_1, ori_list_1 = self.bracket_checker(str(ans))
                if error_pos_1:
                    for pos in error_pos_1:
                        brac_error_pos.append((i, pos))
                    brac_ori_list.extend(ori_list_1)
                error_pos_2, ori_text_2, cor_text_2 = self.check_full_width(str(ans))
                if error_pos_2:
                    for pos in error_pos_2:
                        fw_error_pos.append((i,pos))
                    fw_ori_list.extend(ori_text_2)
                    fw_cor_list.extend(cor_text_2)
                error_pos_3, ori_text_3, cor_text_3 = self.web_format_check(str(ans))
                if error_pos_3:
                    for pos in error_pos_3:
                        web_error_pos.append((i,pos))
                    web_ori_list.extend(ori_text_3)
                    web_cor_list.extend(cor_text_3)
                error_sents_4, ori_text_4, cor_text_4 = self.ch_punc_check(str(ans))
                if error_sents_4:
                    punc_error_sents.extend(error_sents_4)
                    punc_ori_list.extend(ori_text_4)
                    punc_cor_list.extend(cor_text_4)
            if brac_error_pos:
                des = "答案文本存在括号/引号不匹配，错误位置：{}，对应错误符号：{}".format(brac_error_pos, brac_ori_list)
                source = None
                target = None
                pos = None
                _type = "括号/引号不匹配错误"
                replace = 0
                ans_brac = make_dict(des, source, target, pos, _type, replace)
                ans_detail_list.append(ans_brac)
            if fw_error_pos:
                des = "答案文本存在全半角英文字符混用"
                source = fw_ori_list
                target = fw_cor_list
                pos = fw_error_pos
                _type = "全半角字符混用错误"
                replace = 1
                ans_fw = make_dict(des, source, target, pos, _type, replace)
                ans_detail_list.append(ans_fw)
            if web_error_pos:
                des = "答案文本存在网址格式错误"
                source = web_ori_list
                target = web_cor_list
                pos = web_error_pos
                _type = "网址格式错误"
                replace = 1
                ans_web = make_dict(des, source, target, pos, _type, replace)
                ans_detail_list.append(ans_web)
            if punc_error_sents:
                des = "答案文本存在中英文符号混用，错误符号：{}，建议修改：{}，错误句子：{}".format(punc_ori_list, punc_cor_list, punc_error_sents)
                source = None
                target = None
                pos = None
                _type = "中英文符号混用错误"
                replace = 0
                ans_punc = make_dict(des, source, target, pos, _type, replace)
                ans_detail_list.append(ans_punc)
            # 答案错误汇总
            if ans_detail_list:
                # ans_detail_list = order_list(ans_detail_list)
                ans_error_dict["error_sent"] = "answers"
                ans_error_dict["error_detail"] = ans_detail_list
                tid_error_list.append(ans_error_dict)
        
        # 检查解答
        slt_error_dict = dict()
        slt_detail_list = list()
        if solutions:
            solutions = get_recursively_list(solutions)
            brac_error_pos = list() # 存括号检查结果
            brac_ori_list = list()
            fw_error_pos = list() # 存全半角检查结果
            fw_ori_list = list()
            fw_cor_list = list()
            web_error_pos = list() # 存网址检查结果
            web_ori_list = list()
            web_cor_list = list()
            punc_error_sents = list() # 存中英文符号检查结果
            punc_ori_list = list()
            punc_cor_list = list()
            for i, slt in enumerate(solutions): # 检查括号
                error_pos_1, ori_list_1 = self.bracket_checker(str(slt))
                if error_pos_1:
                    for pos in error_pos_1:
                        brac_error_pos.append((i, pos))
                    brac_ori_list.extend(ori_list_1)
                error_pos_2, ori_text_2, cor_text_2 = self.check_full_width(str(slt))
                if error_pos_2:
                    for pos in error_pos_2:
                        fw_error_pos.append((i,pos))
                    fw_ori_list.extend(ori_text_2)
                    fw_cor_list.extend(cor_text_2)
                error_pos_3, ori_text_3, cor_text_3 = self.web_format_check(str(slt))
                if error_pos_3:
                    for pos in error_pos_3:
                        web_error_pos.append((i,pos))
                    web_ori_list.extend(ori_text_3)
                    web_cor_list.extend(cor_text_3)
                error_sents_4, ori_text_4, cor_text_4 = self.ch_punc_check(str(slt))
                if error_sents_4:
                    punc_error_sents.extend(error_sents_4)
                    punc_ori_list.extend(ori_text_4)
                    punc_cor_list.extend(cor_text_4)
            if brac_error_pos:
                des = "解答文本存在括号/引号不匹配，错误位置：{}，对应错误符号：{}".format(brac_error_pos, brac_ori_list)
                source = None
                target = None
                pos = None
                _type = "括号/引号不匹配错误"
                replace = 0
                slt_brac = make_dict(des, source, target, pos, _type, replace)
                slt_detail_list.append(slt_brac)
            if fw_error_pos:
                des = "解答文本存在全半角英文字符混用"
                source = fw_ori_list
                target = fw_cor_list
                pos = fw_error_pos
                _type = "全半角字符混用错误"
                replace = 1
                slt_fw = make_dict(des, source, target, pos, _type, replace)
                slt_detail_list.append(slt_fw)
            if web_error_pos:
                des = "解答文本存在网址格式错误"
                source = web_ori_list
                target = web_cor_list
                pos = web_error_pos
                _type = "网址格式错误"
                replace = 1
                slt_web = make_dict(des, source, target, pos, _type, replace)
                slt_detail_list.append(slt_web)
            if punc_error_sents:
                des = "解答文本存在中英文符号混用，错误符号：{}，建议修改：{}，错误句子：{}".format(punc_ori_list, punc_cor_list, punc_error_sents)
                source = None
                target = None
                pos = None
                _type = "中英文符号混用错误"
                replace = 0
                slt_punc = make_dict(des, source, target, pos, _type, replace)
                slt_detail_list.append(slt_punc)
            # 解答错误汇总
            if slt_detail_list:
                # slt_detail_list = order_list(slt_detail_list)
                slt_error_dict["error_sent"] = "solutions"
                slt_error_dict["error_detail"] = slt_detail_list
                tid_error_list.append(slt_error_dict)
        if tid_error_list:
            format_error_dict[tid] = tid_error_list
            return format_error_dict
        return format_error_dict

        
class NltkTool:
    '''
    nltk工具
    '''
    def __init__(self):
        self.dict_file = r'english_check/en_data/all_words.txt'
        nltk.data.path.append(r"english_check/en_data/packages")
    
    def filter_multi_word(self, dict_path, multi_word_save_path):
        """Filter out the multi-word vocabularies and save"""
        # 如果文件本来存在，先清空
        if os.path.exists(multi_word_save_path):
            with open(multi_word_save_path, 'r+', encoding='utf-8') as f:
                f.seek(0)
                f.truncate() 
        with open(dict_path,'r',encoding='utf-8') as rf:
            for line in rf.readlines():
                word = re.findall(r'[\S]+',line)
                if len(word)>1:
                    with open(multi_word_save_path,'a') as af:
                        af.write(' '.join(word)+'\n')

    def get_multi_word_list(self):
        """Tranform a multi-word vocabulary list to the nltk acceptable form"""
        dict_file = self.dict_file
        multi_word_list = []
        with open(dict_file,'r', encoding='utf-8') as rf:
            for line in rf.readlines():
                word = re.findall(r'[\S]+',line)
                if len(word)>1:
                     multi_word_list.append(tuple(word))            
        return multi_word_list

    def sent_seg(self, text):
        """Seperate a text into setences"""
        punkt_param = PunktParameters()
        abbreviation = ['mr','no','ph','www','dr','etc','Ltd']
        punkt_param.abbrev_types = set(abbreviation)
        tokenizer = PunktSentenceTokenizer(punkt_param)
        result = tokenizer.tokenize(text)
        return result

    def word_seg(self,sentence,multi_word_list):
        """Seperate a sentence into words"""
        tokenizer = MWETokenizer(multi_word_list,separator=' ')
        # token_list = nltk.word_tokenize(sentence)
        token_list = tokenizer.tokenize(nltk.word_tokenize(sentence))
        return token_list

    def word_pos(self,words):
        """词性标注+命名实体识别"""
        tagged = nltk.pos_tag(words)
        chunked = nltk.ne_chunk(tagged)
        entity = list()
        entity_str = str()
        for tagged_tree in chunked:
            if hasattr(tagged_tree,'label'):
                entity_type = tagged_tree.label()
                if entity_type == 'PERSON':
                    entity_name = ' '.join(c[0] for c in tagged_tree.leaves())
                    entity.append(entity_name)
        if entity:
            entity_str = ' '.join(entity)
        return entity_str

    def check_pos(self,token_list):
        """词性标注功能测试"""
        NER_list = list()
        if len(token_list)>1:
            token_list = list(filter(None,token_list))
            pos_res = self.word_pos(token_list)
            NER_list.append(pos_res)
        # print(NER_list)
        NER_list = list(set(NER_list))
        return NER_list

class EnchantTool:
    '''
    Enchant工具
    '''
    def __init__(self):
        # 2020.12.31更新代码
        self.dict_file = r'english_check/en_data/all_words.txt'
        log_server.logging('Loading default dicts...')
        self.GB_dict = enchant.Dict("en_GB")
        self.US_dict = enchant.Dict("en_US")
        self.FR_dict = enchant.Dict("fr_FR")
        log_server.logging('Adding user dict...')
        for word in get_dict_list(self.dict_file):
            self.US_dict.add_to_session(word)
        log_server.logging('Dict loaded!')
        self.pyt = PyTrie()
        self.pyt.setup()
        self.nt = NltkTool()
        self.multi_word_list = self.nt.get_multi_word_list()
        self.st = SequenceTagger()

    def add_temp_dict(self,text):
        """对句中非开头的大写单词和引号内的单词添加临时词典"""
        # todo 在预处理阶段去掉这些词代替加词典
        word_list = text.split(' ') # 非精准切词，只是为了快
        for i, word in enumerate(word_list):
            if word:
                res = re.search(r"[\"]([a-zA-Z-']+)[\"]",word)
                if res:
                    self.US_dict.add_to_session(res[1])
                elif word[0].isupper() and i > 0:
                    self.US_dict.add_to_session(word)


    def check_sent(self,sent):
        err_list = list()
        checker_US = SpellChecker("en_US")
        checker_US.set_text(sent)
        for err in checker_US:
            err_list.append(err.word)
        return err_list

    def norm_check(self,word):
        """拼写检查器1-不对词作任何处理直接检查"""
        flag_1 = self.US_dict.check(word)
        if flag_1 == True:
            return True
        else:
            flag_2 = self.GB_dict.check(word)
            if flag_2 == True:
                return True
            else:
                flag_3 = self.FR_dict.check(word)
                if flag_3 == True:
                    return True
                else:
                    return False

    def quote_check(self,word):
        """拼写检查器2-去掉词开头的引号再检查"""
        if re.findall(r"^[\'\.]",word):
            word = re.sub(r'^[\'\.]','',word)
            return self.norm_check(word)
        else:
            return False

    def hyphen_check(self,word):
        """拼写检查器3-按“-”分词再检查"""
        if '-' in word:
            sub_words = word.split('-')
            sub_words = list(filter(None,sub_words))
            if len(sub_words) > 1:
                for sub in sub_words:
                    if self.norm_check(sub) == False:
                        return False
                    else:
                        continue
                return True
            else:
                return False
        else:
            return False

    def capital_check(self,word):
        """拼写检查器5-按大写分词再检查"""
        sub_words = get_recursively_word_split(word)
        sub_words = list(filter(None,sub_words))
        if len(sub_words) > 1:
            for sub in sub_words:
                if self.norm_check(sub) == False:
                    if '-' in sub:
                        flag = self.hyphen_check(sub)
                        if flag == True:
                            continue
                        else:
                            return False
                    else:
                        return False
                else:
                    continue
            return True
        else:
            return False

    def psfix_check(self,word):
        """拼写检查器6-检查单词是否为带前后缀的复合词"""
        res1 = re.search(r"^(ab|anti|auto|bi|co|de|dis|eco|fore|hemi|im|inter|macro|micro|mis|multi|over|poly|post|pre|re|semi|sub|sur|trans|ultra|un|low|super|nano|self||mal|quad|hyper|flexo|non)",word.lower())
        res2 = re.search(r"(es|s|less)$",word.lower())
        res3 = re.search(r"([\.][a-z])$",word.lower())
        if res1:
            trun_index = res1.span()[1]
            sub_word = word[trun_index:]
            if len(sub_word) > 1:
                if self.norm_check(sub_word) == True:
                    return True
                else:
                    return False
            else:
                return False
        elif res2:
            trun_index = res2.span()[0]
            sub_word = word[:trun_index]
            if len(sub_word) > 1:
                if self.norm_check(sub_word) == True:
                    return True
                else:
                    return False
            else:
                return False
        elif res3:
            trun_index = res3.span()[0]
            sub_word = word[:trun_index]
            if len(sub_word) > 1:
                if self.norm_check(sub_word) == True:
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def tail_check(self,word):
        """拼写检查器7-去掉末尾的一个大写字母"""
        res = re.search(r'[A-Z]$',word)
        if res:
            new_word = word[:-1]
            if len(new_word) > 1:
                if self.norm_check(new_word) == True:
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False
    
    def pinyin_check(self,word):
        """拼写检查器8-检查词是否为拼音"""
        if self.pyt.scan(word.lower()):
            word = re.sub(r'[\']','',word)
            sub_word = self.pyt.scan(word.lower())
            if 'invalid' in sub_word:
                return False
            else:
                return True
        else:
            return False

    def word_sgt(self, word_list):
        """输出错词和对应修改建议的元组列表"""
        # error_detail_list = []
        # error_word = []
        err_words = list()
        sgt_words = list()
        for word in word_list:
            # err_detail = dict()
            if self.norm_check(word) == True:
                continue
            elif self.quote_check(word) == True:
                continue
            elif self.hyphen_check(word) == True:
                continue
            elif self.capital_check(word) == True:
                continue
            elif self.psfix_check(word) == True:
                continue
            elif self.tail_check(word) == True:
                continue
            elif self.pinyin_check(word) == True:
                continue
            else:
                sgt_list = self.US_dict.suggest(word)
                if sgt_list:
                    sgt = sgt_list[0]
                    edit_len = Levenshtein.distance(word, sgt)
                    if edit_len > 3:
                        continue
                    else:
                        # if word[-1].isupper() == False:
                        # err_detail['error_type'] = 'Check spelling'
                        # err_detail['description'] = '拼写错误：请检查单词 {}，建议改为 {}'.format(word,sgt)
                        # error_detail_list.append(err_detail)
                        err_words.append(word)
                        sgt_words.append(sgt)
                else:
                    continue
        return err_words,sgt_words

    def check_text(self, text):
        all_res = list()
        NER_list = list()
        ### step 1. 预处理
        text = spell_check_preprocess(text)
        ### step 2. 分句
        seg_text = self.nt.sent_seg(text)
        ### step 3. 分词
        for sent_init in seg_text:
            if re.search(r"[a-zA-Z]+",sent_init):
                sent_err_list = self.check_sent(sent_init)
                if sent_err_list:
                    sent = re.sub(r"^[a-zA-Z][\.]",'',sent_init)
                    sent = sent.strip()
                    self.add_temp_dict(sent)
                    token_list = self.nt.word_seg(sent, self.multi_word_list)
                    if token_list:
                        # print("token list", token_list)
                        ### step 4. 过滤分词后的token
                        word_list = list()
                        # 分开带省略号的词
                        for index,token in enumerate(token_list):
                            if "…" in token:
                                token = token.split("…")
                                token_list[index] = token
                        token_list = get_recursively_list(token_list)
                        # NER
                        NER_sent = ' '.join(token_list)
                        NER_sent = re.sub(r"``","\"",NER_sent) # nltk的这个分词方法会把双引号替换成``和''，需要替换回正常格式避免影响NER质量
                        NER_sent = re.sub(r"\'\'","\"",NER_sent)
                        NER_list.extend(self.st.tagging(NER_sent))
                        # 过滤含汉字数字网址邮箱音标的单词
                        word_list = filt_word(token_list)
                        # print("word_list", word_list)
                        ### step 5. 拼写检查
                        if len(word_list) > 0:
                            word_list = list(filter(None,word_list))
                            err_words, sgt_words = self.word_sgt(word_list)
                            if err_words:
                                all_res.append((sent_init, err_words, sgt_words))
                    else:
                        continue
                else:
                    continue
            else:
                continue
        # NER_str = ' '.join(NER_list)
        NER_list = list(set(NER_list))
        filt_err_words = list()
        filt_sgt_words = list()
        err_sents = list()
        for res in all_res:
            sent_err_words = list()
            sent_sgt_words = list()
            err_words = res[1]
            sgt_words = res[2]
            for i, word in enumerate(err_words):
                if word not in NER_list:
                    sent_err_words.append(word)
                    sent_sgt_words.append(sgt_words[i])
            if sent_err_words:
                err_sents.append(res[0])
                filt_err_words.extend(sent_err_words)
                filt_sgt_words.extend(sent_sgt_words)
        return err_sents, filt_err_words, filt_sgt_words

    def spell_checker(self,query):
        """拼写检查入口"""
        spell_error_dict = dict()
        spell_error_list = list()
        # tid_error_list = list()
        tid, question, _, stems, _, _ = parse_data(query)
        ques_error_dict = dict()
        # 检查大题干
        err_sents, filt_err_words, filt_sgt_words = self.check_text(question)
        if err_sents:
            des = "请检查大题干文本单词拼写，错误单词：{}，建议修改为：{}，错误句子：{}".format(filt_err_words, filt_sgt_words, err_sents)
            source = None
            target = None
            pos = None
            _type = "英文拼写错误"
            replace = 0
            err_detail = [make_dict(des, source, target, pos, _type, replace)]
            ques_error_dict["error_sent"] = "description"
            ques_error_dict["error_detail"] = err_detail
            spell_error_list.append(ques_error_dict)
        # 检查小题干
        stems_error_dict = dict()
        if stems:
            stem_err_sents = list()
            stem_err_words = list()
            stem_sgt_words = list()
            for stem_dict in stems:
                err_sents, filt_err_words, filt_sgt_words = self.check_text(stem_dict["stem"])
                stem_err_sents.extend(err_sents)
                stem_err_words.extend(filt_err_words)
                stem_sgt_words.extend(filt_sgt_words)
            if stem_err_sents:
                des = "请检查小题干文本单词拼写，错误单词：{}，建议修改为：{}，错误句子：{}".format(stem_err_words, stem_sgt_words, stem_err_sents)
                source = None
                target = None
                pos = None
                _type = "英文拼写错误"
                replace = 0
                err_detail = [make_dict(des, source, target, pos, _type, replace)]
                stems_error_dict["error_sent"] = "stems"
                stems_error_dict["error_detail"] = err_detail
                spell_error_list.append(stems_error_dict)
        if spell_error_list:
            spell_error_dict[tid] = spell_error_list
        return spell_error_dict

class SequenceTagger():
    '''
    tensorflow框架的BiLSTM-CRF-NER模型
    '''
    def __init__(self):
        # create instance of config
        self.config = Config()
        
        # build model
        self.model = NERModel(self.config)
        self.model.build()
        self.model.restore_session(self.config.dir_model)

    def tagging(self,sent):
        # predict
        words_raw = sent.strip().split(" ")
        preds = self.model.predict(words_raw)
        zipped = zip(words_raw,preds)
        NER_list = list()
        tar_tags = ['B-PER', 'I-PER', 'B-LOC', 'I-LOC', 'B-ORG', 'I-ORG', 'B-MISC', 'I-MISC']
        for word,tag in zipped:
            if tag in tar_tags:
                NER_list.append(word)

        return NER_list

class PyTrieNode(object):
    '''
    拼写切割的功能类
    '''
    def __init__(self, key="", seq=[]):
        self.key = key
        self.end = len(seq) == 0
        self.children = {}
        if len(seq) > 0:
            self.children[seq[0]] = PyTrieNode(seq[0], seq[1:])

    def add(self, seq):
        if len(seq) == 0:
            self.end = True
        else:
            key = seq[0]
            value = seq[1:]
            if key in self.children:
                self.children[key].add(value)
            else:
                self.children[key] = PyTrieNode(key, value)

    def find(self, sent):
        for i in range(len(sent)):
            i = len(sent) - i
            if len(sent) >= i:
                key = sent[:i]
                if key in self.children:
                    buf, succ = self.children[key].find(sent[i:])
                    if succ:
                        return key + buf, True
        return "", self.end


class PyTrie(object):
    '''
    拼音切割入口
    '''
    def __init__(self):
        self.root = PyTrieNode()
        self.root.end = False

    def setup(self):
        self.add(["a"])
        self.add(["ai"])
        self.add(["an"])
        self.add(["ang"])
        self.add(["ao"])
        self.add(["e"])
        self.add(["ei"])
        self.add(["en"])
        self.add(["er"])
        self.add(["o"])
        self.add(["ou"])
        self.add(["b", "a"])
        self.add(["b", "ai"])
        self.add(["b", "an"])
        self.add(["b", "ang"])
        self.add(["b", "ao"])
        self.add(["b", "ei"])
        self.add(["b", "en"])
        self.add(["b", "eng"])
        self.add(["b", "i"])
        self.add(["b", "ian"])
        self.add(["b", "iao"])
        self.add(["b", "ie"])
        self.add(["b", "in"])
        self.add(["b", "ing"])
        self.add(["b", "o"])
        self.add(["b", "u"])
        self.add(["c", "a"])
        self.add(["c", "ai"])
        self.add(["c", "an"])
        self.add(["c", "ang"])
        self.add(["c", "ao"])
        self.add(["c", "e"])
        self.add(["c", "en"])
        self.add(["c", "eng"])
        self.add(["c", "i"])
        self.add(["c", "ong"])
        self.add(["c", "ou"])
        self.add(["c", "u"])
        self.add(["c", "uan"])
        self.add(["c", "ui"])
        self.add(["c", "un"])
        self.add(["c", "uo"])
        self.add(["ch", "a"])
        self.add(["ch", "ai"])
        self.add(["ch", "an"])
        self.add(["ch", "ang"])
        self.add(["ch", "ao"])
        self.add(["ch", "e"])
        self.add(["ch", "en"])
        self.add(["ch", "eng"])
        self.add(["ch", "i"])
        self.add(["ch", "ong"])
        self.add(["ch", "ou"])
        self.add(["ch", "u"])
        self.add(["ch", "uai"])
        self.add(["ch", "uan"])
        self.add(["ch", "uang"])
        self.add(["ch", "ui"])
        self.add(["ch", "un"])
        self.add(["ch", "uo"])
        self.add(["d", "a"])
        self.add(["d", "ai"])
        self.add(["d", "an"])
        self.add(["d", "ang"])
        self.add(["d", "ao"])
        self.add(["d", "e"])
        self.add(["d", "eng"])
        self.add(["d", "i"])
        self.add(["d", "ia"])
        self.add(["d", "ian"])
        self.add(["d", "iao"])
        self.add(["d", "ie"])
        self.add(["d", "ing"])
        self.add(["d", "iu"])
        self.add(["d", "ong"])
        self.add(["d", "ou"])
        self.add(["d", "u"])
        self.add(["d", "uan"])
        self.add(["d", "ui"])
        self.add(["d", "un"])
        self.add(["d", "uo"])
        self.add(["f", "a"])
        self.add(["f", "an"])
        self.add(["f", "ang"])
        self.add(["f", "ei"])
        self.add(["f", "en"])
        self.add(["f", "eng"])
        self.add(["f", "o"])
        self.add(["f", "ou"])
        self.add(["f", "u"])
        self.add(["g", "a"])
        self.add(["g", "ai"])
        self.add(["g", "an"])
        self.add(["g", "ang"])
        self.add(["g", "ao"])
        self.add(["g", "e"])
        self.add(["g", "ei"])
        self.add(["g", "en"])
        self.add(["g", "eng"])
        self.add(["g", "ong"])
        self.add(["g", "ou"])
        self.add(["g", "u"])
        self.add(["g", "ua"])
        self.add(["g", "uai"])
        self.add(["g", "uan"])
        self.add(["g", "uang"])
        self.add(["g", "ui"])
        self.add(["g", "un"])
        self.add(["g", "uo"])
        self.add(["h", "a"])
        self.add(["h", "ai"])
        self.add(["h", "an"])
        self.add(["h", "ang"])
        self.add(["h", "ao"])
        self.add(["h", "e"])
        self.add(["h", "ei"])
        self.add(["h", "en"])
        self.add(["h", "eng"])
        self.add(["h", "ong"])
        self.add(["h", "ou"])
        self.add(["h", "u"])
        self.add(["h", "ua"])
        self.add(["h", "uai"])
        self.add(["h", "uan"])
        self.add(["h", "uang"])
        self.add(["h", "ui"])
        self.add(["h", "un"])
        self.add(["h", "uo"])
        self.add(["j", "i"])
        self.add(["j", "ia"])
        self.add(["j", "ian"])
        self.add(["j", "iang"])
        self.add(["j", "iao"])
        self.add(["j", "ie"])
        self.add(["j", "in"])
        self.add(["j", "ing"])
        self.add(["j", "iong"])
        self.add(["j", "iu"])
        self.add(["j", "u"])
        self.add(["j", "uan"])
        self.add(["j", "ue"])
        self.add(["j", "un"])
        self.add(["k", "a"])
        self.add(["k", "ai"])
        self.add(["k", "an"])
        self.add(["k", "ang"])
        self.add(["k", "ao"])
        self.add(["k", "e"])
        self.add(["k", "en"])
        self.add(["k", "eng"])
        self.add(["k", "ong"])
        self.add(["k", "ou"])
        self.add(["k", "u"])
        self.add(["k", "ua"])
        self.add(["k", "uai"])
        self.add(["k", "uan"])
        self.add(["k", "uang"])
        self.add(["k", "ui"])
        self.add(["k", "un"])
        self.add(["k", "uo"])
        self.add(["l", "a"])
        self.add(["l", "ai"])
        self.add(["l", "an"])
        self.add(["l", "ang"])
        self.add(["l", "ao"])
        self.add(["l", "e"])
        self.add(["l", "ei"])
        self.add(["l", "eng"])
        self.add(["l", "i"])
        self.add(["l", "ia"])
        self.add(["l", "ian"])
        self.add(["l", "iang"])
        self.add(["l", "iao"])
        self.add(["l", "ie"])
        self.add(["l", "in"])
        self.add(["l", "ing"])
        self.add(["l", "iu"])
        self.add(["l", "ong"])
        self.add(["l", "ou"])
        self.add(["l", "u"])
        self.add(["l", "u:"])
        self.add(["l", "ue"])
        self.add(["l", "uan"])
        self.add(["l", "un"])
        self.add(["l", "uo"])
        self.add(["m", ""])
        self.add(["m", "a"])
        self.add(["m", "ai"])
        self.add(["m", "an"])
        self.add(["m", "ang"])
        self.add(["m", "ao"])
        self.add(["m", "e"])
        self.add(["m", "ei"])
        self.add(["m", "en"])
        self.add(["m", "eng"])
        self.add(["m", "i"])
        self.add(["m", "ian"])
        self.add(["m", "iao"])
        self.add(["m", "ie"])
        self.add(["m", "in"])
        self.add(["m", "ing"])
        self.add(["m", "iu"])
        self.add(["m", "o"])
        self.add(["m", "ou"])
        self.add(["m", "u"])
        self.add(["n", "a"])
        self.add(["n", "ai"])
        self.add(["n", "an"])
        self.add(["n", "ang"])
        self.add(["n", "ao"])
        self.add(["n", "e"])
        self.add(["n", "ei"])
        self.add(["n", "en"])
        self.add(["n", "eng"])
        self.add(["n", "g"])
        self.add(["n", "i"])
        self.add(["n", "ian"])
        self.add(["n", "iang"])
        self.add(["n", "iao"])
        self.add(["n", "ie"])
        self.add(["n", "in"])
        self.add(["n", "ing"])
        self.add(["n", "iu"])
        self.add(["n", "ong"])
        self.add(["n", "ou"])
        self.add(["n", "u"])
        self.add(["n", "v"])
        self.add(["n", "ue"])
        self.add(["n", "uan"])
        self.add(["n", "uo"])
        self.add(["p", "a"])
        self.add(["p", "ai"])
        self.add(["p", "an"])
        self.add(["p", "ang"])
        self.add(["p", "ao"])
        self.add(["p", "ei"])
        self.add(["p", "en"])
        self.add(["p", "eng"])
        self.add(["p", "i"])
        self.add(["p", "ian"])
        self.add(["p", "iao"])
        self.add(["p", "ie"])
        self.add(["p", "in"])
        self.add(["p", "ing"])
        self.add(["p", "o"])
        self.add(["p", "ou"])
        self.add(["p", "u"])
        self.add(["q", "i"])
        self.add(["q", "ia"])
        self.add(["q", "ian"])
        self.add(["q", "iang"])
        self.add(["q", "iao"])
        self.add(["q", "ie"])
        self.add(["q", "in"])
        self.add(["q", "ing"])
        self.add(["q", "iong"])
        self.add(["q", "iu"])
        self.add(["q", "u"])
        self.add(["q", "uan"])
        self.add(["q", "ue"])
        self.add(["q", "un"])
        self.add(["r", "an"])
        self.add(["r", "ang"])
        self.add(["r", "ao"])
        self.add(["r", "e"])
        self.add(["r", "en"])
        self.add(["r", "eng"])
        self.add(["r", "i"])
        self.add(["r", "ong"])
        self.add(["r", "ou"])
        self.add(["r", "u"])
        self.add(["r", "uan"])
        self.add(["r", "ui"])
        self.add(["r", "un"])
        self.add(["r", "uo"])
        self.add(["s", "a"])
        self.add(["s", "ai"])
        self.add(["s", "an"])
        self.add(["s", "ang"])
        self.add(["s", "ao"])
        self.add(["s", "e"])
        self.add(["s", "en"])
        self.add(["s", "eng"])
        self.add(["s", "i"])
        self.add(["s", "ong"])
        self.add(["s", "ou"])
        self.add(["s", "u"])
        self.add(["s", "uan"])
        self.add(["s", "ui"])
        self.add(["s", "un"])
        self.add(["s", "uo"])
        self.add(["sh", "a"])
        self.add(["sh", "ai"])
        self.add(["sh", "an"])
        self.add(["sh", "ang"])
        self.add(["sh", "ao"])
        self.add(["sh", "e"])
        self.add(["sh", "ei"])
        self.add(["sh", "en"])
        self.add(["sh", "eng"])
        self.add(["sh", "i"])
        self.add(["sh", "ou"])
        self.add(["sh", "u"])
        self.add(["sh", "ua"])
        self.add(["sh", "uai"])
        self.add(["sh", "uan"])
        self.add(["sh", "uang"])
        self.add(["sh", "ui"])
        self.add(["sh", "un"])
        self.add(["sh", "uo"])
        self.add(["t", "a"])
        self.add(["t", "ai"])
        self.add(["t", "an"])
        self.add(["t", "ang"])
        self.add(["t", "ao"])
        self.add(["t", "e"])
        self.add(["t", "eng"])
        self.add(["t", "i"])
        self.add(["t", "ian"])
        self.add(["t", "iao"])
        self.add(["t", "ie"])
        self.add(["t", "ing"])
        self.add(["t", "ong"])
        self.add(["t", "ou"])
        self.add(["t", "u"])
        self.add(["t", "uan"])
        self.add(["t", "ui"])
        self.add(["t", "un"])
        self.add(["t", "uo"])
        self.add(["w", "a"])
        self.add(["w", "ai"])
        self.add(["w", "an"])
        self.add(["w", "ang"])
        self.add(["w", "ei"])
        self.add(["w", "en"])
        self.add(["w", "eng"])
        self.add(["w", "o"])
        self.add(["w", "u"])
        self.add(["x", "i"])
        self.add(["x", "ia"])
        self.add(["x", "ian"])
        self.add(["x", "iang"])
        self.add(["x", "iao"])
        self.add(["x", "ie"])
        self.add(["x", "in"])
        self.add(["x", "ing"])
        self.add(["x", "iong"])
        self.add(["x", "iu"])
        self.add(["x", "u"])
        self.add(["x", "uan"])
        self.add(["x", "ue"])
        self.add(["x", "un"])
        self.add(["y", "a"])
        self.add(["y", "an"])
        self.add(["y", "ang"])
        self.add(["y", "ao"])
        self.add(["y", "e"])
        self.add(["y", "i"])
        self.add(["y", "iao"])
        self.add(["y", "in"])
        self.add(["y", "ing"])
        self.add(["y", "o"])
        self.add(["y", "ong"])
        self.add(["y", "ou"])
        self.add(["y", "u"])
        self.add(["y", "uan"])
        self.add(["y", "ue"])
        self.add(["y", "un"])
        self.add(["z", "a"])
        self.add(["z", "ai"])
        self.add(["z", "an"])
        self.add(["z", "ang"])
        self.add(["z", "ao"])
        self.add(["z", "e"])
        self.add(["z", "ei"])
        self.add(["z", "en"])
        self.add(["z", "eng"])
        self.add(["z", "i"])
        self.add(["z", "ong"])
        self.add(["z", "ou"])
        self.add(["z", "u"])
        self.add(["z", "uan"])
        self.add(["z", "ui"])
        self.add(["z", "un"])
        self.add(["z", "uo"])
        self.add(["zh", "a"])
        self.add(["zh", "ai"])
        self.add(["zh", "an"])
        self.add(["zh", "ang"])
        self.add(["zh", "ao"])
        self.add(["zh", "e"])
        self.add(["zh", "en"])
        self.add(["zh", "eng"])
        self.add(["zh", "i"])
        self.add(["zh", "ong"])
        self.add(["zh", "ou"])
        self.add(["zh", "u"])
        self.add(["zh", "ua"])
        self.add(["zh", "uai"])
        self.add(["zh", "uan"])
        self.add(["zh", "uang"])
        self.add(["zh", "ui"])
        self.add(["zh", "un"])
        self.add(["zh", "uo"])

    def add(self, seq):
        self.root.add(seq)

    def scan(self, sent):
        words = []
        while len(sent) > 0:
            buf, succ = self.root.find(sent)
            # print("buf: {}, succ: {}".format(buf, succ))
            if succ:
                words.append(buf)
                sent = sent[len(buf):]
            else:
                # words.append('invalid:' + sent[0])
                words.append('invalid')
                sent = sent[1:]
        return words

