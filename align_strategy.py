# !/usr/bin/python3
# -*- coding:utf-8 -*-
# @Author : dyu
# @Time   : 2020-11-2
# @Modify : 2020-11-7
# @Function : 对齐策略

import os

class AlignStrategy(object):
    def __init__(self):
        pass

    def parse(self, info):
        """
        解析错误
        :return:
        """
        error_values = list(info.values())[0]
        for ln in error_values:
            sent = ln['error_sent']
            print(sent)


    def merge(self):
        """
        针对同一文本有多个错误
        :return:
        """
        pass

    def recombine(self):
        """
        重新组合数据格式
        :return:
        """
        pass

if __name__ == '__main__':
    define_data = {'123123': [{'error_sent':'你好！！', 'error_detail':[{"error_type": 'spell_error', "description": '号'}, {"error_type": 'symbol_error', "description": None}]}]}
    aligh = AlignStrategy()
    aligh.parse(define_data)

