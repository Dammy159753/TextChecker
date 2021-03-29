#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time   : 2020/12/16 - 17:00
# @Modify : 2020/12/16 - 17:00
# @Author : dyu
# @File : ancient_classification.py
# @Function : 辨古识今

import numpy as np
from xgboost.sklearn import XGBClassifier
from gensim.models import Word2Vec
import pickle
import re

class AncientClassifier(object):
    """ 辨古识今 """
    def __init__(self):
        self.pattern_symbol = re.compile(r'[,，.。!！?？:：\"“”<>《》……(（）){}]')
        self.ancient_p = re.compile('[之乎者也焉矣盖耳吾尔]')
        self.modern_p = re.compile('[着了过的嗯你他]')
        self.digital = re.compile('[a-zA-Z0-9@#￥$%&*]+')
        self.model = Word2Vec.load('chinese_check/ancient_chinese/ancient_w2v.model')
        with open('chinese_check/ancient_chinese/ancient_xgb.model', 'rb') as f:
            self.clf = pickle.load(f)

    def embed(self, text):
        """
        char embedding
        :return: vector
        """
        counts, row = 0, 0
        for char in text:
            try:
                if char != ' ':
                    row += self.model.wv[char]
                    counts += 1
            except:
                pass
        if counts != 0:
            vec = row / counts
            return vec
        else:
            return None

    def ml_predict(self, text, alpha):
        """
        ML predictor
        :return:  T/F
        """
        if self.embed(text) is not None:
            vec = self.embed(text)
            label = self.clf.predict(vec.reshape(1, -1))
            proba = self.clf.predict_proba(vec.reshape(1, -1))
            if proba[:,1] > alpha:
                return 1, proba
            else:
                return 0, proba
        else:
            return 0, 0

    def detect(self, text, alpha=0.6):
        """
        :return:  True is ancient, False is modern
        """
        clean_text = re.sub(self.pattern_symbol, ' ', text).strip()
        tag, proba = self.ml_predict(clean_text, alpha)
        if len(re.findall(self.digital, text)) == 0:
            if tag == 1:
                return True
        else:
            return False

if __name__ == '__main__':
    text = "从加那调州, 今缅甸丹那沙林, 乘大拍，张七帆，时风一月余，乃入秦，大秦国也"
    ancient = AncientClassifier()
    # ancient.detect(text))
    # ancient.predict(text)


