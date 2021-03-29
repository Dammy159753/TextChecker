# !/usr/bin/python3
# -*- coding:utf-8 -*-
# @Author : dyu
# @Time   : 2019-12-30 18:42
import re
import json
from tqdm import tqdm
from collections import OrderedDict


def read_json(js_f):
    with open(js_f, 'r', encoding='utf-8') as f:
        data = json.load(f, object_pairs_hook=OrderedDict)
    return data

class BaseProcessLatex:
    def __init__(self):
        self.latex_mapping = read_json(r'formula_check/LaTexMap/latex_map.json')

        self.special_pattern = {
            "\pmod{m}": "mod m",
        }


    def train_data_process(self, src_dct):
        """
        将原数据转成顺利格式，经过答案填充及公式映射
        :param src_dct: 原数据
        :return: 处理后的文本文件
        """
        res_question = dict()
        for tid, item in tqdm(src_dct.items()):
            question = item['question']
            trans_question = self.process_latex(question)
            item['question'] = trans_question
            res_question[tid] = item
        return res_question

    def process_latex(self, text):
        """
        对文本进行公式映射及处理
        :param text: 待处理的文本
        :return: 处理好的文本
        """
        text = re.sub(r'\$', '', text)   # 移除latex的开始与结束标记

        text = self.mapping_latex(text)   # 公式映射

        text = self.deal_fraction(text)   # 处理分式

        text = self.unified_format(text)  # 统一格式
        return text

    def rm_mathrm(self, text):
        text = re.sub(r'\\math[a-zA-Z]+', r'', text)
        return text

    def mapping_latex(self, text):
        for latex, sym in self.latex_mapping.items():
            text = text.replace(latex, sym)
        return text

    def deal_fraction(self, text):
        # 处理分式
        while True:
            start_text = text
            text = re.sub(r'(\\d?frac *{[^{}]*?){([^{}]+)}(.*?})', r'\1(\2)\3', text)
            if start_text == text:
                break
        print(text)
        text = re.sub(r'\\d?frac *{(.*?)} *{(.*?)}', r'{\1}/{\2} ', text)
        text = re.sub(r'\\?d?frac *\((.+)\) *\((.+)\)', r'\1/\2 ', text)
        return text

    def unified_format(self, text):
        # 移除花括号
        text = re.sub(r'\\{', r'&&&$', text)
        text = re.sub(r'\\}', r'$&&&', text)
        while True:
            start_text = text
            # 部分括号/花括号移除
            text = re.sub(r'\(([a-z0-9 ]*)\)', r'\1', text)
            text = re.sub(r'\(( *. *)\)', r'\1', text)
            # text = re.sub(r'\{([a-z0-9]*.)\}', r'\1', text)

            text = re.sub(r'{ *([^{}]*?) *}', r' \1 ', text)
            if start_text == text:
                break
        text = re.sub(r'&&&\$', r'{', text)
        text = re.sub(r'\$&&&', r'}', text)

        # 移除多余空格
        text = text.replace('\\xa0', ' ')
        text = re.sub(r' +', ' ', text)  # 多个空格只保留一个空格
        text = re.sub(r' *([\^_−>·()/=×<~≤≥∠≠△⊥≡±∈～°。.，,∼⇌⇒→⇓↓λΛαβμξγδΔ′•\-+⋅]+) *', r'\1', text)
        text = re.sub(r'[（()] *[)）]', '', text)

        # 替换剩余的特殊符号
        text = text.replace('&gt;', '≥')
        text = text.replace('&lt;', '<')
        text = text.replace('&amp;', '')
        text = text.replace('&', '')

        text = re.sub(r'\\xrightarrow\[\\,\]', '', text)
        text = re.sub('cases(.*?)cases', r'分段函数\1', text)
        text = re.sub(r' *\^?°', r'°', text)
        text = re.sub('\^°C', '℃', text)
        text = text.replace('^′', '′')
        text = re.sub(r'\\', '', text)
        text = text.replace(r'\\\\', '或')
        text = text.replace('，', ',')
        text = re.sub(r'([,。 ])+', r'\1', text)
        text = re.sub(r'([\u4e00-\u9fa5]) ([\u4e00-\u9fa5])', r'\1\2', text)

        text = re.sub(r'([_^])([0-9]{2,}) ', r'\1(\2)', text)
        text = re.sub(r'([_^])([0-9]) ', r'\1\2', text)

        # ∫dx 定积分符号提取
        text = re.sub(r'∫(.*?)dx', r'定积分\1', text)

        # ^2 变成“二次方”
        text = re.sub(r'cm\^2', '平方厘米', text)
        text = re.sub(r'\^2', '的二次方', text)
        return text

base = BaseProcessLatex()
