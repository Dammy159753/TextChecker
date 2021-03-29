# !/usr/bin/python3
# -*- coding:utf-8 -*-
# @Author : dyu
# @Time   : 2020-05-22 10:42

""" 爱云校分词器 """
from data_processing import seg_tool
import re, json, os


def segment(grade_subject, query):
    query_seg = seg_tool.word_segment(grade_subject=grade_subject, query=query)
    return query_seg 
    
if __name__ == "__main__":
    query = "用化学用语填空： （1）${ 2}$个碳原子【${2\\mathrm C}$】 ； （2）${ 3}$个氮分子【${3{\\mathrm N}_2}$】； （3）${ 5}$个钠离子【${5\\mathrm{Na}^+}$】 ； （4）${ +6}$价硫元素的氧化物【${{\\mathrm{SO}}_3}$】； （5）标出氧化铝中铝元素的化合价【${\\overset{}{{\\overset{+3}{\\mathrm{Al}}}_2{\\mathrm O}_3}}$】； （6）氦元素【${\\mathrm{He}}$】"
    print("source: ", query)
    print(segment("junior_chemistry", query))
    # pass
