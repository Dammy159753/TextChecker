# !/usr/bin/python3
# -*- coding:utf-8 -*-
# @Author : dengyu
# @Time   : 2020/02/15

##################################################################################################
##                                       Segment Function                                       ##
##                                                                                              ##
##################################################################################################

from .word_segment import sentence_split
from .deal_chemistry import read_sentences
from .math_segment import SegTool

def word_seg(query):
    """
    Word segment function
    :paramter :
    """
    segTool = SegTool(stopwords_path='./dataset/stopword.txt')
    sentences = segTool.cutSent(query)
    if len(sentences) == 1:
        result = segTool.segWords(sentences[0])
    else:
        result = segTool.segWords(" ".join(sentences))
    return result

def word_segment(grade_subject, query):
    """ 各科目分词方法 """
    words = ' '.join(query)
    grade_subject = grade_subject.split('_')
    if 'math' in grade_subject or 'history' in grade_subject:
        words = word_seg(query=query)
    elif 'physics' in grade_subject:
        if 'senior' in grade_subject:
            words = read_sentences(query)
            words = ' '.join(words)
        else:
            words = sentence_split(query, use_stopwords=True)
            words = ' '.join(words)
    elif 'chemistry' in grade_subject:
        words = read_sentences(query)
        words = ' '.join(words)

    elif 'biology' in grade_subject or 'geography' in grade_subject or 'politics' in grade_subject:
        words = sentence_split(query, use_stopwords=True)
        words = ' '.join(words)
    return words