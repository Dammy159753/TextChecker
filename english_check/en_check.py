#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# @File    :   en_check.py
# @Time    :   2020/11/12
# @update  :   2020/12/2
# @Author  :   dyu

from en_utils import spell_check_preprocess, rm_point_zero, NltkTool, EnchantTool, FormatChecker, get_recursively_list, filt_word, SequenceTagger, parse_data, merge_dicts, make_dict
import os
import re
import time
import json
from tqdm import tqdm
from collections import Counter
from check_match import MatchChecker
from logserver import log_server
from GEC_check.GEC_server import standalone_test


class EnCheck(object):
    def __init__(self, mode):
        self.mode = mode
        self.mc = MatchChecker()
        self.et = EnchantTool()
        self.nt = NltkTool()
        self.multi_word_list = self.nt.get_multi_word_list()
        self.st = SequenceTagger()
        self.fc = FormatChecker()
        log_server.logging("Init en_checker over!")

    def checker(self, grade, subject, query):
        """
        英语检查器入口
        :param query:
        :return:
        """
        log_server.logging(">>> Enter en_checker !")
        all_error_dict = dict()
        grade_subject = grade + '_' + subject
        ### step1 解析数据 ###
        tid, _, _, _, _, _ = parse_data(query)
        if self.mode == 'all functions':
            ### step2 符号检查 ###
            try:
                symbol_error_dict = self.check_symbol_format(query)
            except Exception as e:
                log_server.logging('Symbol check exception: {}'.format(e))
                symbol_error_dict = dict()
            ### step3 拼写检查 ###
            try:
                spell_error_dict = self.check_spell(query)
            except Exception as e:
                log_server.logging('Spell check exception: {}'.format(e))
                spell_error_dict = dict()
            ### step4 检查答案与解答是否对应 ###
            try:
                unmatch_error_dict = self.check_match(query, grade_subject)
            except Exception as e:
                log_server.logging('Check match exception: {}'.format(e))
                unmatch_error_dict = dict()
            ### step5 语法检查 ###
            try:
                grammar_error_dict = self.check_grammar(query)
            except Exception as e:
                log_server.logging('Grammar check exception: {}'.format(e))
                grammar_error_dict = dict()
            ############################### 第四步 错误类型汇总 ################################
            all_error_dict = merge_dicts(tid, symbol_error_dict, spell_error_dict, unmatch_error_dict, grammar_error_dict)
            log_server.logging('Finish en checker! All error dict saved.')
            return all_error_dict
        elif self.mode == 'check symbol and full-width':
            all_error_dict = self.check_symbol_format(query)
            return all_error_dict
        elif self.mode == 'check spell':
            all_error_dict = self.check_spell(query)
            return all_error_dict
        elif self.mode == 'check match':
            all_error_dict = self.check_match(query, grade_subject)
            return all_error_dict
        elif self.mode == 'check grammar':
            all_error_dict = self.check_grammar(query)
            return all_error_dict
        else:
            return all_error_dict


    def check_symbol_format(self, query):
        """
        符号、格式和全半角检查
        :param query:
        :return:
        """
        log_server.logging(">>> checking symbol and full-width error ")
        start_time = time.time()
        symbol_error_dict = self.fc.format_checker(query)
        end_time = time.time()
        log_server.logging('Symbol and full-width check finish and saved! Total time is {} >>>'.format(end_time - start_time))
        return symbol_error_dict

    def check_spell(self, query):
        """
        检查英文拼写(NER采用LSTM)
        """
        log_server.logging('>>> checking spelling error ')
        start_time = time.time()
        spell_error_dict = self.et.spell_checker(query)
        end_time = time.time()
        log_server.logging('Spelling check finish! Total time is {} >>>'.format(end_time-start_time))
        # write_to_json(all_error_dict, error_save_file)
        return spell_error_dict        

    def check_match(self, query, grade_subject):
        """
        匹配答案解析等各种对应关系质检
        :param query:
        :return:
        """
        log_server.logging(">>> Checking matching error")
        start_time = time.time()
        unmatch_error_dict = dict()
        unmatch_error_dict = self.mc.parser(query, grade_subject)
        end_time = time.time()
        log_server.logging('Matching check finish and saved! Total time is {} >>>'.format(end_time-start_time))
        return unmatch_error_dict

    def check_grammar(self, query):
        '''
        name: 语法检查器
        msg: 目前只检查书面表达的答案和阅读理解的题目，并且句子必须为完整句子
        param query
        return grammar_error_dict
        '''
        tid, question, answers, stems, solutions, _type = parse_data(query)
        grammar_error_dict = dict()
        # tid_error_list = list()
        if _type == "书面表达":
            if len(answers) == 1 and isinstance(answers[0],str):
                text = spell_check_preprocess(answers[0],rm_underline=False,rm_ch=True)
                des_list, err_sents = standalone_test(text)
                if des_list:
                    ans_err_dict = dict()
                    des = "英文语法错误，修改建议：{}，错误句子：{}".format(des_list, err_sents)
                    source = None
                    target = None
                    pos = None
                    _type = "英文语法错误"
                    replace = 0
                    ans_err_dict["error_sent"] = "answers"
                    ans_err_dict["error_detail"] = [make_dict(des, source, target, pos, _type, replace)]
                    grammar_error_dict[tid] = [ans_err_dict]
                    return grammar_error_dict
        elif _type == "阅读理解":
            if isinstance(question,str):
                text = spell_check_preprocess(question,rm_underline=False,rm_ch=True)
                des_list, err_sents = standalone_test(text)
                if des_list:
                    ques_err_dict = dict()
                    des = "英文语法错误，修改建议：{}，错误句子：{}".format(des_list, err_sents)
                    source = None
                    target = None
                    pos = None
                    _type = "英文语法错误"
                    replace = 0
                    ques_err_dict["error_sent"] = "description"
                    ques_err_dict["error_detail"] = [make_dict(des, source, target, pos, _type, replace)]
                    grammar_error_dict[tid] = [ques_err_dict]
                    return grammar_error_dict
        # if len(tid_error_list) > 0:
        #     grammar_error_dict[tid] = tid_error_list
        return grammar_error_dict

    def summarize(self, query, symbol_error_dict, spell_error_dict, unmatch_error_dict):
        """
        总结错误
        :param symbol_error_dict:
        :param spell_error_dict:
        :param unmatch_error_dict:
        :return:
        """
        log_server.logging('>>>>>Start summarize all error type<<<<<')
        tid, question, answers, opts, solutions, _type = parse_data(query)
        # keys = symbol_error_dict.keys()
        # for key in tqdm(spell_error_dict.keys()):
        #     if key in keys:
        #         symbol_error_dict[key].extend(spell_error_dict[key])
        #     else:
        #         symbol_error_dict[key] = spell_error_dict[key]
        # for key in tqdm(unmatch_error_dict.keys()):
        #     if key in keys:
        #         symbol_error_dict[key].extend(unmatch_error_dict[key])
        #     else:
        #         symbol_error_dict[key] = unmatch_error_dict[key]
        all_error_dict = dict()
        all_error_list = list()
        if len(symbol_error_dict) > 0:
            all_error_list.extend(symbol_error_dict[tid])
        if len(spell_error_dict) > 0:
            all_error_list.extend(spell_error_dict[tid])
        if len(unmatch_error_dict) > 0:
            all_error_list.extend(unmatch_error_dict[tid])
        all_error_dict[tid] = all_error_list
        print(all_error_dict)
        print('Finish summarizing! All error dict saved.')
        return all_error_dict
