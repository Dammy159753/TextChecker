#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time   : 2020/11/17 - 17:03
# @Modify : 2020/12/18 - 16:30
# @Author : dyu
# @File : latex_utils.py
# @Function : 公式检测的工具类


import re
import os
import json
import re
import os
import json
import codecs
import subprocess
import latex2mathml.converter
from collections import OrderedDict, Counter

# from sympy import sympify
# from sympy.parsing.latex import parse_latex
from tex_check import TexChecker
from LaTexMap import latex_parser
latexer = latex_parser.BaseProcessLatex()


def fm_read_json(js_f):
    with open(js_f, 'r', encoding='utf8') as f:
        data = json.load(f, object_pairs_hook=OrderedDict)
    return data


def latex2sym(latex):
    """
    Convert Latex to sym
    :param text:
    :return:
    """
    # f = sympify(text[1:-1])
    expr = parse_latex(latex)
    return expr


def latex_translation(latex):
    """
    latex2content 解析
    :param latex:
    :return:
    """
    trans_latex = latexer.process_latex(latex)
    return trans_latex


def extract_formula(text):
    """
    Extract formulas in text
    :param text:
    :return:
    """
    latex_p = re.compile(r"(?<=\$\{).*?(?=\}\$)")
    latexs = re.findall(latex_p, text)
    return latexs


def remove_char(str, start_index, end_index):
    front = str[:start_index]  # up to but not including n
    back = str[end_index + 1:]  # n+1 till the end of string
    return front + back


def bracket_fm(string):
    """ 检测{}公式 """
    stack = []
    index_record = []
    bracket_list = list()
    for index,char in enumerate(string):
        # 如果是左括号
        if char == '{' and index != 0:
            if string[index-1] != '$':
                # 入栈
                stack.append([char,index])
                # print('left',stack)
        # 右括号
        elif char == '}' and index != len(string)-1: 
            if string[index+1] != '$':
                # 如果stack长度为1，此右括号是公式结束符，返回一条完整公式，然后出栈
                if len(stack) == 1 and stack[0][0] == '{':
                    # print('end_right',char)
                    end_index = index
                    start_index = stack[0][1]
                    bracket_list.append(string[start_index:end_index+1])
                    index_record.append([start_index,end_index])
                    stack.pop()
                # 如果不是公式结束，只出栈
                elif stack and stack[-1][0] == '{':
                    # 出栈
                    stack.pop()

    return bracket_list,stack,index_record


def correct_fm(string):
    """ 检测{}公式 """
    stack = []
    index_record = []
    bracket_list = list()
    for index,char in enumerate(string):
        # 如果是左括号
        if char == '{' and index != 0:
            if string[index-1] == '$':
                # 入栈
                stack.append([char,index])
                # print('left',stack)
        # 右括号
        elif char == '}' and index != len(string)-1:
            if string[index+1] == '$':
                if stack and stack[-1][0] == '{':
                # 如果stack长度为1，此右括号是公式结束符，返回一条完整公式，然后出栈
                    end_index = index
                    start_index = stack[-1][1]-1
                    bracket_list.append(string[start_index:end_index+1])
                    index_record.append([start_index,end_index+1])
                    stack.pop()

    return index_record


def indexstr(str1,str2):
    '''查找指定字符串str1包含指定子字符串str2的全部位置，
    以列表形式返回'''
    lenth2=len(str2)
    lenth1=len(str1)
    indexstr2=[]
    i=0
    while str2 in str1[i:]:
        indextmp = str1.index(str2, i, lenth1)
        indexstr2.append(indextmp)
        i = (indextmp + lenth2)

    return indexstr2


def latex2sym(text):
    """
    Convert Latex to sym
    :param text:
    :return:
    """
    # f = sympify(text[1:-1])
    expr = parse_latex(text)
    return expr


def extract_formula_old(text):
    """
    Extract formulas in text
    :param text:
    :return:
    """
    latex_p = re.compile(r"(?<=\$\{).*?(?=\}\$)")
    latexs = re.findall(latex_p, text)
    for lax in latexs :
        try:
            expr = latex2sym(lax)
            print("[{}] --> [{}]".format(lax, expr))
        except:
            print("except:", lax)
            pass


### Tool ###
class Scheme_Checker():
    '''
    检查公式格式的功能类
    '''
    def __init__(self):
        '''
        加载latex映射关系字典
        '''
        self.latex_map_file = r'formula_check/latex_map.json'
        with open(self.latex_map_file,'r') as rf:
            self.latex_map = rf.read()
            self.latex_map = json.loads(self.latex_map)
            self.latex_keys = self.latex_map.keys()

    def filter_correct(self,string):
        '''
        过滤格式正确的公，,形如${}$
        '''
        index_record = correct_fm(string)
        filt_sent = string
        if index_record:
            for index in index_record:
                start = index[0]
                end = index[1]
                fm_len = end-start+1
                str_list = list(filt_sent)
                str_list[start:end+1] = '@'*fm_len
                filt_sent = ''.join(str_list)

        return filt_sent

    def check_dollar(self, string):
        '''
        检查带$的公式格式错误
        '''
        # 先过滤掉格式正确的公式，
        filt_sent = self.filter_correct(string)
        sent_error_list = list()
        # 过滤后的文本如果含有$字符，即有公式格式错误
        if '${' in filt_sent:
            symbol_index = indexstr(filt_sent,'${')
            if symbol_index:
                for i in symbol_index:
                    start_index = i
                    end_search = re.search(r'[\.。,，\?？;；!！]',filt_sent[start_index:])
                    if end_search:
                        end_index = end_search.span()[0]
                        error_sent = string[start_index:start_index+end_index]
                    else:
                        error_sent = string[start_index:]
                    error_detail_dict = dict()
                    error_detail_dict["error_type"] = "fm_scheme_error"
                    error_detail_dict["description"] = "公式格式错误，请检查{}".format(error_sent)
                    sent_error_list.append(error_detail_dict)
        elif '}$' in filt_sent:
            symbol_index = indexstr(filt_sent,'}$')
            if symbol_index:
                for i in symbol_index:
                    start_index = i+1
                    end_search = re.search(r'[\.。,，\?？;；!！]',filt_sent[:start_index])
                    if end_search:
                        end_index = end_search.span()[0]
                        error_sent = string[end_index+2:start_index+1]
                    else:
                        error_sent = string[:start_index]
                    error_detail_dict = dict()
                    error_detail_dict["error_type"] = "fm_scheme_error"
                    error_detail_dict["description"] = "公式格式错误，请检查{}".format(error_sent)
                    sent_error_list.append(error_detail_dict)            
        return sent_error_list

    def check_bracket(self,string):
        '''
        检查只带括号{}的格式错误
        '''
        # 先过滤掉格式正确的公式
        filt_sent = self.filter_correct(string)
        sent_error_list = list()
        bracket_list,_,_ = bracket_fm(filt_sent)
        if bracket_list:
            for b in bracket_list:
                for key in self.latex_keys:
                    if key in b:
                        error_detail_dict = dict()
                        error_detail_dict["error_type"] = "fm_scheme_error"
                        error_detail_dict["description"] = "公式{}格式缺失".format(b)
                        sent_error_list.append(error_detail_dict)
                        break
        return sent_error_list

    def check_symbol(self,string):
        '''
        检查文本中只有latex符号，不带$和{}的情况
        '''
        # 先过滤掉带{}的以及正确的公式
        filt_sent = self.filter_correct(string)
        _,_,index_record = bracket_fm(filt_sent)
        index_record = index_record[::-1]
        sent_error_list = list()
        for index in index_record:
            start_index = index[0]
            end_index = index[1]
            filt_sent = remove_char(filt_sent, start_index, end_index)
        for key in self.latex_keys:
            if key in filt_sent:
                error_detail_dict = dict()
                error_detail_dict["error_type"] = "fm_scheme_error"
                error_detail_dict["description"] = "公式{}格式缺失".format(key)
                sent_error_list.append(error_detail_dict)
        return sent_error_list


### Founction_1 ###
class FormatCheck(object):
    def __init__(self):
        self.sc = Scheme_Checker()

    def check_scheme(self,text):
        scheme_error_dict = dict()
        scheme_error_list = list()
        dollar_error = self.sc.check_dollar(text)
        if dollar_error:
            scheme_error_list.extend(dollar_error)
        bracket_error = self.sc.check_bracket(text)
        if bracket_error:
            scheme_error_list.extend(bracket_error)
        if scheme_error_list:
            scheme_error_dict['error_sent'] = text
            scheme_error_dict['error_detail'] = scheme_error_list
            return scheme_error_dict
        else:
            return None

### Founction_2 ###
class Textidote():
    def __init__(self, latex):
        self.cmd = 'textidote test.tex'
        self.result = os.popen(self.cmd).readlines()
        self.latex  = latex
        # res = subprocess.Popen(cmd).communicate()

    def dote_check(self):
        self.read_tex(self.latex)
        err = {}
        if 'Everything is OK!' in ''.join(self.result):
            return None
        else:
            dote = [line.replace('\n', '') for line in self.result]
            indexs = [(m.start(), m.start() + len(m.group())) for m in re.finditer(r'\^+', dote[-1])]
            errors = [[dote[-2][index[0]: index[1]], index]  for index in indexs]
            err['error_type'] = 'fm_content_error'
            err['description'] = "内容错误: {}".format(errors)
            return err

    def read_tex(self, latex):
        with codecs.open('formula_check/test.tex', 'w+', encoding='utf-8') as f :
            lines = f.readlines()
            if len(lines) == 0:
                f.write(latex)
            else:
                f.seek(0)
                f.truncate()

### Founction_3 ###
def check_latex_symbol_repeat(latex):
    """
    检查公式符号重复
    :param latex:
    :return:
    """
    err = {}
    pattern_1 = re.compile(r'\^{2,}|\+{2,}|%{2,}|@{1,}|&{2,}|\*{2,}|\${2,}')  # 待添加
    if re.findall(pattern_1, latex):
        w = [(m.start(), m.start() + len(m.group())) for m in re.finditer(pattern_1, latex)]
        des = [latex[i[0]:i[1]] for i in w]
        err['error_type'] = 'fm_content_error'
        err['description'] = "同一符号出现多次: {}".format(w)
        # err['description'] = "同一符号出现多次: {}".format(des)
        return err
    else:
        return None


### Founction_4 ###
def check_latex_illegal_symbol(latex):
    """
    检查公式非法符号
    :param latex:
    :return:
    """
    err = {}
    pattern_2 = re.compile(r"[\"“”`·《》？：]")
    if re.findall(pattern_2, latex):
        w = [(m.start(), m.start() + len(m.group())) for m in re.finditer(pattern_2, latex)]
        err['error_type'] = 'fm_content_error'
        err['description'] = "未定义符号: {}".format(w)
        return err
    else:
        return None


### Founction_5 ###
def check_latex_func_name(latex, names, subject='math'):
    """
    Check latex function name
    :return:
    """
    error_detail = []  # error set
    pattern_4 = re.compile(r"({.*?})")
    all_funcs = list(names.keys())
    funcs = [f for f in all_funcs if '\\' in f]

    # ## 3.1 如果\\后面有空格，如\\ mathrm
    # tmp_1 = {}
    # if re.findall(r'(\\ {1,})(^\\\\)', latex):
    #     w = [(m.start(), m.start() + len(m.group())) for m in re.finditer(r'(\\ {1,})(^\\\\)', latex)]
    #     # print("Space error: {}".format(w))
    #     tmp_1['error_type'] = 'fm_scheme_error'
    #     tmp_1['description'] = "空格错误: {}".format(w)
    #     error_detail.append(tmp_1)
    rm_e_latex = re.sub(r'(?<=\\)( {1,})', '', latex)

    ## 3.2 校对函数名称(暂时只针对数学)
    if subject == 'math':
        pattern = re.compile(r"(?<=\\)\w+(?= {1,})|(?<=\\)\w+(?={)")
        for m in re.findall(pattern, rm_e_latex):
            tmp_2 = {}
            if '\\' + m not in funcs:
                if m not in re.findall(r'(?<=\\)\d+', rm_e_latex) and m[-1:] != '_' \
                        and m not in re.findall(r'(?<=\\)\w+\d+', rm_e_latex) \
                        and m not in re.findall(r'(?<=\\\\)\w+', rm_e_latex):
                    index = re.search(m, latex).span()
                    # print("Function name error: {}".format(m, index))
                    tmp_2['error_type'] = 'fm_content_error'
                    tmp_2['description'] = "函数名字错误: {}, {}".format(m, index)
            error_detail.append(tmp_2)
    if len(error_detail) != 0:
        return error_detail
    else:
        return None


### Founction_6 ###
def check_latex_brackets(latex):
    """
    检查多种括号错误
    :param latex:
    :return:
    """
    error_detail = dict()
    errors =  list()

    chars = dict(Counter(latex))
    char_k = list(chars.keys())
    smybols = ["{", "}", "(", ")", "[", "]"]
    brackets = [c for c in char_k if c in smybols]

    def judge_pairs_bracket(pairs):
        _pattern = ''
        pattern_curly = re.compile(r'[{}]')
        pattern_circle = re.compile(r'[()]')
        pattern_square = re.compile(r'[\[\]]')
        if pairs == ('{', '}'):
            _pattern = pattern_curly
        elif pairs == ('(', ')'):
            _pattern = pattern_circle
        elif pairs == ('[', ']'):
            _pattern = pattern_square

        if pairs[0] in brackets and pairs[1] in brackets:
            try:
                assert chars[pairs[0]] == chars[pairs[1]]
            except AssertionError:
                w = [(m.start(), m.start() + len(m.group())) for m in re.finditer(_pattern, latex)]
                errors.append("{}{}左右括号数量不对应: {}".format(pairs[0], pairs[1], w))
        elif pairs[0] in brackets or pairs[1] in brackets:
            w = [(m.start(), m.start() + len(m.group())) for m in re.finditer(_pattern, latex)]
            errors.append('{}{}括号缺失只有单边: {}'.format(pairs[0], pairs[1], w))
        else:
            pass

    judge_pairs_bracket(('{', '}'))
    judge_pairs_bracket(('(', ')'))
    judge_pairs_bracket(('[', ']'))

    error_detail['error_type'] = 'fm_scheme_error'
    error_detail['description'] = errors

    if len(errors) != 0:
        return error_detail
    else:
        return None


if __name__ == '__main__':
    pass




