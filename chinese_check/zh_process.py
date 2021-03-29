#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author : yqw,dyu
# @Time: 2020-11-23
# @Function: 中文检错器

import json
import re

import operator as op
from langconv import *
from collections import OrderedDict, Counter

from zh_utils import num_to_ch, postProcess, Chinese_conversion, sortList, bracket, preprocess, split_sentence
from zh_utils import EXCLUSIVE_LIST, PUNCTUATION, FIND_LIST, DIGIT, FW_ALPHABET, ALPHABET_DICT
from zh_config import zh_check_config

class Data_Process(object):
    def __init__(self, subject):
        self.subject = subject
        self.max_conf = zh_check_config['faspell_config'][self.subject]['max_conf']
        self.max_length = zh_check_config['faspell_config'][self.subject]['max_length']

    def numProcess(self, sentence):
        """
        对句子中的阿拉伯数字进行转换， 转换成汉字数字。
        :param sentence:
        :return:
        """
        pattern = re.compile(r'\d+')
        value = re.findall(pattern, sentence)
        if len(value)>0:
            for v in value:
                replace = num_to_ch(v)
                if (v is not None) & (replace is not None):
                    sentence = sentence.replace(v, replace, 1)
        return sentence


    def alignment(self, details, text):
        """
        位置对齐
        :param details:
        :param text:
        :return:
        """
        punc = PUNCTUATION+'+-”“’‘；；：￥、─()＝∴∵．'
        punc = re.compile(r'[{}]'.format(punc))
        source = []
        target = []
        position = []
        for detail in details:
            source.append(detail)
            target.append(details[detail]['Word_suggestion'])
            index = details[detail]['Position']
            substring = re.sub(punc, '@', details[detail]['Original_sentence'])
            text = re.sub(punc, '@', text)
            value = re.search(substring, text)
            if value is not None:
                position.append((value.span()[0]+index, value.span()[0]+index+1))
        return source, target, position


    def specialSymbol(self, text, _ind):
        """
        检查是否有字符使用不规范错误， 并返回位置。
        :param text:
        :param _ind:
        :return:
        """
        htmlPattern = re.compile(r'(html\s*{.*}\s*)')
        if len(re.findall(htmlPattern, text)) > 0:
            text = re.sub(htmlPattern, '', text).strip()
        text = re.sub(r'[(&gt;)(&lt;)]', '', text)
        spe_groups = ['？！', '！？']
        pattern = re.compile(r'[,，.。！!？\?：:；;\.\…]{2,}')
        pattern1 = re.compile(r'[,，.。！!？\?：:；;]*\…{2,}[,，.。！!？\?：:；;]*')
        errors_list = []
        result_list = []
        def find_pos(st):
            if '.' in st or '…' in st:
                index = (text.index(st), text.index(st) + len(st))
            else:
                index = re.search(st, text).span()
            return index

        if (len(re.findall(pattern, text)) != 0):
            errs = re.findall(pattern, text)
            errs = set(errs).difference(set(re.findall(pattern1, text)))
            filter_errs = list(set([i for i in errs if '{' not in i and '}' not in i and '……' != i and '......' != i]))

            if filter_errs:
                index = []
                position = []
                for err in filter_errs:
                    index.append(find_pos(err))
                    # position.append(show_text_value([find_pos(err)], text))

                e, r = sortList(index, filter_errs)
                errors_list = e
                result_list = [[_ind, res] for res in r]

        return errors_list, result_list


    def bracketMatch(self, text,_ind):
        """
        检查是否有符号不匹配的情况， 并返回位置
        :param text:
        :param _ind:
        :return:
        """
        flag, stack = bracket(text)
        symbol = []
        position = []
        if not flag:
            _, result = sortList(stack, None)
            for sta in result:
                symbol.append(sta[1])
                position.append([_ind, (sta[0], sta[0] + 1)])
        return symbol, position


    def enSymbolProcess(self,_ind, cont):
        """
        检查中英文符号使用不规范， 并返回错误
        :param _ind:
        :param cont:
        :return:
        """
        record = []
        replaces = []
        positions = []
        flag = False
        for fw in FW_ALPHABET:
            if fw in cont:
                if re.search(r'[a-zA-Z]', cont) != None:
                    flag = True
                    position = cont.find(fw)
                    while position != -1:
                        record.append(fw)
                        replace = ALPHABET_DICT[fw]
                        replaces.append(replace)
                        positions.append([_ind, (position, position + 1)])
                        cont = cont[:position] + replace + cont[position + 1:]
                        position = cont.find(fw, position + 1)

        return flag, record, replaces, positions


    def wordProcess(self, result):
        """
        对错别字检测进行后处理。
        :param result:
        :param max_conf:
        :return:
        """

        process_list = {}
        for errs in result:
            if len(errs['errors']) > 0:
                for err in errs['errors']:
                    err_index = err['error_position']
                    corr_char = err['corrected_to']
                    orig_char = err['original']

                    if (err['confidence'] > self.max_conf) & (err['similarity'] > 0.6):
                        if 0 < err_index < len(errs['corrected_sentence']) - 1:
                            """当错别字处在句子的中部时， 检查此错别字前部分和后部分是否达标"""
                            pre_char = errs['corrected_sentence'][err_index - 1]
                            post_char = errs['corrected_sentence'][err_index + 1]
                            if not ((corr_char == pre_char) | (corr_char == post_char) | (pre_char + orig_char in EXCLUSIVE_LIST) |
                                    (orig_char in EXCLUSIVE_LIST) | (orig_char + post_char in EXCLUSIVE_LIST)):
                                if postProcess(orig_char, corr_char):
                                    process_list.update({err['original']: {
                                        'Word_suggestion': err['corrected_to'],
                                        'Position': err['error_position'],
                                        'Original_sentence': errs['original_sentence']}})

                        elif err_index == 0:
                            """当错别字处在句子的头部时， 检查此错别字的后部分是否达标"""
                            post_char = errs['corrected_sentence'][err_index + 1]
                            if not ((corr_char == post_char) | (orig_char in EXCLUSIVE_LIST) | (
                                    orig_char + post_char in EXCLUSIVE_LIST)):
                                if postProcess(orig_char, corr_char):
                                    process_list.update( {err['original']:{
                                        'Word_suggestion': err['corrected_to'],
                                        'Position': err['error_position'],
                                        'Original_sentence': errs['original_sentence']}})

                        elif err_index == len(errs['corrected_sentence']) - 1:
                            """当错别字处在句子尾部时， 检查此错别字的前部分是否达标"""
                            pre_char = errs['corrected_sentence'][err_index - 1]
                            if not ((corr_char == pre_char) | (orig_char in EXCLUSIVE_LIST) | (
                                    pre_char + orig_char in EXCLUSIVE_LIST)):
                                if postProcess(orig_char, corr_char):
                                    process_list.update({err['original']: {
                                        'Word_suggestion': err['corrected_to'],
                                        'Position': err['error_position'],
                                        'Original_sentence': errs['original_sentence']}})
        return process_list


    def tradProcess(self, sentence, _ind):
        """
        判断文本编码是否为big5hkscs，如是为繁体字，报错为简体字
        todo type_error == 'trad_zh_error'
        :param text:
        :param error_type :
        :return:
        """
        error_detail = []
        try:
            sentence.encode('big5hkscs')
            return []
        except UnicodeEncodeError:
            simplified = Chinese_conversion(sentence)
            if op.ne(sentence.encode('utf-8'), simplified.encode('utf-8')):
                indexs = [[(i, simplified[int(m.start())], m.start(), _ind) for m in re.finditer(i, sentence)]
                          for i in [c for c in sentence if c not in simplified]]
                for i in indexs:
                    error_detail.extend(i)
                error_detail = list(set(error_detail))
                error_detail.sort(key=lambda x: x[2])
            return error_detail


    def spell_check(self, value_list,ancient, spellchecker):
        """
        对分句后的句子进行检查是否有错别字和繁体字的存在。
        并对其进行后处理，且返回错误集的信息内容
        :param value_list:
        :param max_length:
        :param ancient:
        :param spellchecker:
        :return:
        """
        """繁体字检测"""
        errors_detail = {}

        for ques in value_list:
            """辩古识今：文言文提取"""
            if not ancient.detect(ques):

                """错别字检测"""
                data = preprocess(ques)
                """把阿拉伯数字转换成汉字数字"""
                data = self.numProcess(data)
                """如若句子长度超过最大序列长度，或者短于10， 将不进行错词检测。"""
                if (len(data) < self.max_length) & (len(data) > 10):
                    result = spellchecker.make_corrections([data])
                    """对错别字检测结果进行后处理"""
                    error_detail = self.wordProcess(result)
                    errors_detail.update(error_detail)

        return errors_detail


    def spell_process(self, text, _ind, ancient, spellchecker, original, tradWord):
        """
        检查繁体字的存在， 检查错别字的存在， 并返回内容与位置信息
        :param text:
        :param _ind:
        :param max_length:
        :param ancient:
        :param spellchecker:
        :param original:
        :return:
        """
        if tradWord:
            trad_list = self.tradProcess(text, _ind)
        else:
            trad_list = []
        text_split = split_sentence(text)
        error_detail = self.spell_check(text_split, ancient, spellchecker)
        if len(error_detail) > 0 and (trad_list is not None) or len(trad_list)>0:
            for trads in trad_list:
                if trads[0] in error_detail.keys():
                    if trads[2] == error_detail[trads[0]]['Position']:
                        trad_list.remove(trads)

        text = preprocess(original)
        text = self.numProcess(text)
        source, target, p = self.alignment(error_detail, text)
        position = [[_ind, pos] for pos in p]

        return trad_list, source, target, position

    def ocr_spell_process(self, error_detail):
        error_set = dict()
        source, target, position = [], [], []
        original = list(error_detail.items())[0][1]['Original_sentence']
        corrected = list(error_detail.items())[0][1]['Original_sentence']
        for errors in error_detail:
            source.append(errors)
            target.append(error_detail[errors]['Word_suggestion'])
            pos = error_detail[errors]['Position']
            position.append((pos, pos+1))
            corrected = corrected[:pos] + error_detail[errors]['Word_suggestion']+corrected[pos+1:]
        error_set.update({
            'original':original,
            'corrected':corrected,
            'source':source,
            'target':target,
            'position':position,
            'error_type':'字词错误'
        })

        return error_set