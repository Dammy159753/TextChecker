#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time   : 2020/11/24 - 15:28
# @Modify : 2020/12/16 - 18:20
# @Author : dyu
# @File : check_controller.py
# @Function : Textchecker 的控制器

import os
import time
import sys
sys.path.append("chinese_check")
sys.path.append("english_check")
sys.path.append("formula_check")
sys.path.append("Faspell")

from LAC import LAC
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import re
from logserver import log_server
from conf import config
from chinese_check.zh_check import ZhCheck
from english_check.en_check import EnCheck

#from formula_check.fm_checker import FmChecker
from Faspell.faspell import SpellChecker
from chinese_check.ancient_chinese.ancient_classification import AncientClassifier
from chinese_check.zh_utils import split_sentence, preprocess
from chinese_check.zh_process import Data_Process

class Controller(object):
    def __init__(self):
        log_server.logging('===============Init Checker!===============')
        self.tradWordDetect = config["zh_check_config"]['chinese_textQ_config']["tradWordDetect"]
        self.wrongWordDetect = config["zh_check_config"]['chinese_textQ_config']["wrongWordDetect"]
        self.keywordMatch = config["zh_check_config"]['chinese_textQ_config']["keywordMatch"]
        self.contentMatch = config["zh_check_config"]['chinese_textQ_config']["contentMatch"]
        self.symbolCheck = config["zh_check_config"]['chinese_textQ_config']["symbolCheck"]
        self.typeMatch = config["zh_check_config"]['chinese_textQ_config']["typeMatch"]
        self.contTypeMatch = config["zh_check_config"]['chinese_textQ_config']["contTypeMatch"]
        self.enSymbolDetect = config["zh_check_config"]['chinese_textQ_config']["enSymbolDetect"]
        self.serialCheck = config["zh_check_config"]['chinese_textQ_config']["serialCheck"]

        log_server.logging('>>> 1.Zh_checker Initializing !')
        self.lac_mode = LAC(mode=config["zh_check_config"]['lac_segment']['lac_mode'])
        self.lac_mode.load_customization(config["zh_check_config"]['lac_segment']['word_loc'])
        self.ancient = AncientClassifier()

        self.com_spellchecker = SpellChecker(config['faspell_config']["literal"]['model'], config['faspell_config']["literal"]['max_seq_length'])
        self.bio_spellchecker = SpellChecker(config['faspell_config']["biology"]['model'], config['faspell_config']["biology"]['max_seq_length'])
        self.science_spellchecker = SpellChecker(config['faspell_config']["science"]['model'], config['faspell_config']["science"]['max_seq_length'])

        log_server.logging(self.com_spellchecker)
        log_server.logging('Zh_checker Initialization over ! >>>')

        log_server.logging('>>> 2.En_checker Initializing !')
        self.en_selection_mode = ['check symbol and full-width', 'check spell', 'check match','check grammar', 'all functions']
        self.en_checker = EnCheck(self.en_selection_mode[4])
        log_server.logging('En_checker Initialization over ! >>>')

        log_server.logging('>>> 3.Fm_checker Initializing !')
        self.fm_mode = ['symbol_repeat', 'illegal_symbol', 'func_name', 'brackets', 'latex2mathml', 'texcheck', 'textidote', 'LaTeXEqChecker', 'mathJax']
        self.fm_select_mode = ['func_name', 'symbol_repeat', 'latex2mathml', 'textidote', 'illegal_symbol']
        # self.latex_checker = FmChecker(self.fm_select_mode)
        self.re_ = re.compile(r'(\\rm)|</?[^<>]+>')
        log_server.logging('Fm_checker Initialization over ! >>>')

        log_server.logging('=============Init Checker Over!=============')


    def parse(self, data):
        """
        根据不同 grade、subject 调用相应的检查器进行质检
        :param data:
        :return:
        """
        log_server.logging('====== Allocation Checker! ======')
        grade, subject, query = data['grade'], data['subject'], data['query']

        query = self.text_filter(query)
        if subject in ['history', 'politics','chinese']:
            faspell = self.com_spellchecker
        elif subject in ['biology']:
            faspell = self.bio_spellchecker
        elif subject in ['physics','math','chemistry']:
            faspell = self.science_spellchecker
        else:
            faspell = None

        #modified

        if subject == 'english':
            en_error_set = self.en_checker.checker(grade, subject, query)
            return en_error_set
        else:
            self.zh_checker = ZhCheck(dictionary=query, subject=config['trans_subject'][subject], lac=self.lac_mode,
                                      faspell=faspell, ancient=self.ancient)
            zh_position, zh_error_set = [], []
            #modified
            p, errors = self.zh_checker(tradWordDetect=self.tradWordDetect,
                                        wrongWordDetect=self.wrongWordDetect,
                                        keywordMatch=self.keywordMatch,
                                        contentMatch=self.contentMatch,
                                        symbolCheck=self.symbolCheck,
                                        typeMatch=self.typeMatch,
                                        contTypeMatch = self.contTypeMatch,
                                        enSymbolDetect = self.enSymbolDetect,
                                        serialCheck = self.serialCheck)
            if len(p) > 0:
                zh_position.append(p)
            if len(errors) > 0:
                zh_error_set.append(errors)

            return zh_error_set


    def parse_spellDetect(self, data):
        """
        解析数据， 进行错词检测。
        :param data:
        :return:
        """
        error_detail = dict()
        log_server.logging('====== Allocation spell Detect! ======')
        zh_error_set = []
        subject, query = data['subject'], data['query']
        query = self.text_filter(query)

        if subject in ['history', 'politics','chinese']:
            faspell = self.com_spellchecker
        elif subject in ['biology']:
            faspell = self.bio_spellchecker
        elif subject in ['physics','math','chemistry']:
            faspell = self.science_spellchecker
        else:
            faspell = None

        subject = config['trans_subject'][subject]

        for ques in query:
            ques = split_sentence(ques)
            process = Data_Process(subject)
            for que in ques:
                if not self.ancient.detect(que):
                    data = preprocess(que)
                    data = process.numProcess(data)
                    if (len(data) < 100) & (len(data) > 10):
                        result = faspell.make_corrections([data])
                        """对错别字检测结果进行后处理"""
                        error_detail = process.wordProcess(result)
                        if len(error_detail)>0:
                            zh_error_set.append(process.ocr_spell_process(error_detail))

        log_server.logging('====== Spell Detect Finished! ======')
        error_detail['error_detail'] = zh_error_set
        return error_detail


    def text_filter(self, obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                obj[key] = self.text_filter(value)
        elif isinstance(obj, list):
            for index, value in enumerate(obj):
                obj[index] = self.text_filter(value)
        elif isinstance(obj, str):
            return self.re_.sub(' ', obj).replace('&nbsp;', ' ')
        return obj


class CheckofChinese():
    def __init__(self, query, subject):
        super(CheckofChinese, self).__init__()
        self.query = query
        self.subject = subject

    def call(self):
        pass


class CheckofEnglish():
    def __init__(self, query, subject):
        super(CheckofChinese, self).__init__()
        self.query = query
        self.subject = subject

    def call(self):
        pass


class CheckofLatex():
    def __init__(self, query, subject):
        super(CheckofChinese, self).__init__()
        self.query = query
        self.subject = subject

    def call(self):
        pass

if __name__ == '__main__':
    Controller()
