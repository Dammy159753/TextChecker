#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time   : 2020/11/23 - 18:22
# @Modify : 2020/11/23 - 18:22
# @Author : dyu
# @File : conf.py
# @Function :


config = dict(
    predictor=[
        'senior_chemistry',
        'junior_chemistry',
        'senior_math',
        'junior_math',
        'senior_physics',
        'junior_physics',
        'senior_geography',
        'junior_geography',
        'senior_politics',
        'junior_politics',
        'senior_history',
        'junior_history',
        'senior_biology',
        'junior_biology',
        'senior_english',
        'junior_english',
        'senior_chinese',
        'junior_chinese',
    ],

    trans_subject=dict(
        math="数学",
        physics="物理",
        chemistry="化学",
        biology="生物",
        politics="政治",
        history="历史",
        geography="地理",
        chinese="语文",
        english="英语",
    ),

    RETURN_CODE=dict(
        OK=0,
        URL_ERROR=1,
        AUTH_ERROR=2,
        PARAMETERS_ERROR=3,
        HANDLE_ERROR=4,
        NULL_ERROR=5,
        CONNTECTION_TIMEOUT=6,
        DATA_FORMAT_ERROR=7,
    ),

    RETURN_MSG=dict(
        OK='ok',
        URL_ERROR='api not found',
        AUTH_ERROR='authentication error',
        PARAMETERS_ERROR='parameters error',
        HANDLE_ERROR='server error',
        NULL_ERROR='en_data error',
        CONNTECTION_TIMEOUT='connection timeout',
        DATA_FORMAT_ERROR='please check input en_data.',
    ),

    zh_check_config = dict({
        "chinese_textQ_config": {
            "wrongWordDetect": True,
            "tradWordDetect": True,
            "symbolCheck": True,
            "typeMatch": True,
            "contTypeMatch":True,
            "enSymbolDetect":True,
            "serialCheck":True,
            "contentMatch": False,
            "keywordMatch": True,
        },
        "lac_segment": {
            "lac_mode": "lac",
            "seg_mode": "seg",
            "word_loc": "chinese_check/zh_data/all_words_vocab_20201124.txt"
        },
    }),

    faspell_config = dict({
        "literal":{
            'model':'/model/model.ckpt-20',
            'max_seq_length':90
        },
        "biology":{
            'model':'/model/model.ckpt-20',
            'max_seq_length':100
        },
        "geography":'',
        "science":{
            'model':'/model/science/model.ckpt-10000',
            'max_seq_length':100
        }
    })
)
