#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/11/6 17:46
# @Author : yqw, dyu
# @File : config.py


zh_check_config = dict({
      "error_type": {
        "zh_type_unmatch_error": '题目题型不匹配错误',
        "zh_type_style_unmatch_error": '题目格式错误',
        "zh_symbol_error": '符号使用不当错误',
        "zh_symbol_error_1": "符号使用不当错误",
        "zh_format_error": "空格过多错误",
        "zh_serial_unmatch_error": "小题号错误",
        "zh_enSymbol_unmatch_error": "中文全半角混用错误",
        "zh_spell_error": "字词错误",
        "zh_font_error": "繁简字错误",
        "zh_answer_unmatch_error":"答案A与故选A匹配错误",
        "zh_qos_unmatch_error":"题干与解答内容匹配错误",
        "zh_qas_unmatch_error":"题干与解答内容匹配错误",
        "zh_answer_unmatch_error_1":"√×不匹配错误"
      },
      "description":{
        "zh_symbol_error_1":"特殊符号混用;",
        "zh_format_error":"解答中空格过多。",
        "zh_symbol_error":"括号，引号不匹配;",
        "zh_font_error":'繁体字检测, 检测到句子中有繁体字的使用情况， 请检查是否正确。原句：{}',
        "zh_spell_error":"错别字检测, 检测到句子中有错别字的使用情况， 请检查是否正确。原句：{}",
        "zh_type_unmatch_error": {
          "选择题":"题目题型不匹配，此题型为：{}; 选项不能为空",
          "判断题":"题目题型不匹配，此题型为：{}; 答案中没有匹配到关键字，例如√×。位置:{}",
          "非选择题":"题目题型不匹配，此题型为：{}; 但内容为选择题。",
          "非判断题":"题目题型不匹配，此题型为：{}; 但内容为判断题。"
        },
        "zh_type_style_unmatch_error":{
          "选择题":{
            "解答":"题目格式不正确，解答中所有内容不能为空",
            "答案":"题目格式不正确，此题型为：{}; 答案中没有匹配到关键字A-Z。"
          },
          "判断题":"题目格式不正确，此题型为：{}; 答案匹配不到关键字或关键字使用不规范，判断对错的关键字只能使用“√/×”或“正确/不正确/错误”。[说明： 额外的关键字， 生物：‘T/F’, 地理：‘对/错’]"
        },
        "zh_enSymbol_unmatch_error":"{}中全半角英文字符混用",
        "zh_serial_unmatch_error":"{}中有小题号缺失; 或小题号格式不完整; 或小题号格式不统一， 请检查。[说明： 只接受格式（1）/(1)] 。位置：{} 缺少小题号({})"

      },
      "faspell_config":{
        "语文":{
          "max_conf":0.85,
          "max_length":60
        },
        "生物":{
          "max_conf":0.85,
          "max_length":90
        },
        "历史":{
          "max_conf":0.8,
          "max_length":90
        },
        "政治": {
          "max_conf": 0.8,
          "max_length":100
        },
        "地理": {
          "max_conf": 0.85,
          "max_length": 100
        },
        "物理": {
          "max_conf": 0.7,
          "max_length": 100
        },
        "化学": {
          "max_conf": 0.85,
          "max_length": 100
        },
        "数学": {
          "max_conf": 0.8,
          "max_length": 120
        }

      }
})

