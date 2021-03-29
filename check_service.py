#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time   : 2020/11/23 - 17:54
# @Modify : 2020/11/23 - 17:54
# @Author : dyu
# @File : check_service.py
# @Function : 文本质检服务接口

import json
import os
import time
import sys
sys.path.append("chinese_check")
sys.path.append("english_check")
import tracemalloc
from conf import config
from flask import Flask, jsonify, request
from check_controller import Controller
from logserver import log_server
tracemalloc.start()

__version__ = '1.0'
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = True

# Init Controller
controller = Controller()

def check_param(post_json):
    """
    字段检测，key是否存在，类型是否正常等
    """
    # 1. 核对科目信息是否符合要求
    if "grade" in post_json and "subject" in post_json:
        grade = post_json['grade']
        subject = post_json['subject']
        grade_subject = grade + '_' + subject
        if grade_subject not in config['predictor']:
            return False
    else:
        return False

    # 2. 核对请求数据内容是否含有必选参数
    required_keys = ["_id",'description', 'stems', 'labels', 'answers', 'type', 'solutions', 'explanations']
    if 'query' in post_json and post_json['query']:
        # 2 判断query字典的数据完整性

        item = post_json['query']
        # 2.1 判断question里字段完整性 和 字段是否是None
        for r_key in required_keys:
            if r_key not in item.keys() or item[r_key] is None:
                return False

        # 2.2 判断question里字段的类型
        if not all((isinstance(item['_id'], float)  or isinstance(item['_id'], int),
                    isinstance(item['description'], str), isinstance(item['stems'], list),
                    isinstance(item['labels'], list), isinstance(item['type'], str),
                    isinstance(item['answers'], list) or isinstance(item['answers'], str),
                    isinstance(item['solutions'], list), isinstance(item['explanations'], list))):
            return False
        return True
    else:
        return False

def check_param_1(post_json):
    """
    字段检测，key是否存在，类型是否正常等
    """
    # 1. 核对科目信息是否符合要求
    if "subject" in post_json:
        subject = post_json['subject']
        grade_subject = 'junior_' + subject
        if grade_subject not in config['predictor']:
            return False
    else:
        return False
    if 'query' in post_json and post_json['query']:
        if not isinstance(post_json['query'], list):
            return False
        return True
    else:
        return False

@app.route('/text_quality_check', methods=['POST'])
def text_quality_check():
    """
    Main Interface Route
    """
    log_server.logging('============Enter Checker System !===========')
    result = {'code': config['RETURN_CODE']['OK'], 'message': config['RETURN_MSG']['OK'], 'en_data': dict()}

    try:
        post_data = request.data
        # step1: 数据编码校验
        if isinstance(post_data, bytes):
            post_data = post_data.decode()
        query_json = json.loads(post_data)
    except Exception as e:
        log_server.logging('Please check input en_data: {}'.format(e))
        result['code'] = config['RETURN_CODE']['DATA_FORMAT_ERROR']
        result['message'] = config['RETURN_MSG']['DATA_FORMAT_ERROR']
        return jsonify(result)

    # step2: 数据格式校验
    if not check_param(query_json):
        log_server.logging('Data Format Error: {}'.format(query_json))
        result['code'] = config['RETURN_CODE']['PARAMETERS_ERROR']
        result['message'] = config['RETURN_MSG']['PARAMETERS_ERROR']
        return jsonify(result)

    # step3: 开始检测
    pre_start = time.time()
    try:
        ### 这里是检测的入口 ###
        check_result = controller.parse(query_json)
    except Exception as e:
        log_server.logging('Predict Error: {}'.format(e))
        result['code'] = config['RETURN_CODE']['HANDLE_ERROR']
        result['message'] = config['RETURN_MSG']['HANDLE_ERROR']
        return jsonify(result)

    pre_end = time.time()
    result['data'] = check_result
    log_server.logging('>>>>>>>> Time of the whole process: {:.6f}'.format(pre_end - pre_start))
    log_server.logging('============Exit Checker System !===========')
    return jsonify(result)



@app.route('/tqc_spell_check', methods=['POST'])
def tqc_spell_check():
    """
    Main Interface Route
    """
    log_server.logging('============Enter Spell Checker System !===========')
    result = {'code': config['RETURN_CODE']['OK'], 'message': config['RETURN_MSG']['OK'], 'en_data': dict()}

    try:
        post_data = request.data
        # step1: 数据编码校验
        if isinstance(post_data, bytes):
            post_data = post_data.decode()
        query_json = json.loads(post_data)
    except Exception as e:
        log_server.logging('Please check input en_data: {}'.format(e))
        result['code'] = config['RETURN_CODE']['DATA_FORMAT_ERROR']
        result['message'] = config['RETURN_MSG']['DATA_FORMAT_ERROR']
        return jsonify(result)

    # step2: 数据格式校验
    if not check_param_1(query_json):
        log_server.logging('Data Format Error: {}'.format(query_json))
        result['code'] = config['RETURN_CODE']['PARAMETERS_ERROR']
        result['message'] = config['RETURN_MSG']['PARAMETERS_ERROR']
        return jsonify(result)

    # step3: 开始检测
    pre_start = time.time()
    try:
        ### 这里是检测的入口 ###
        check_result = controller.parse_spellDetect(query_json)
    except Exception as e:
        log_server.logging('Predict Error: {}'.format(e))
        result['code'] = config['RETURN_CODE']['HANDLE_ERROR']
        result['message'] = config['RETURN_MSG']['HANDLE_ERROR']
        return jsonify(result)

    pre_end = time.time()
    result['data'] = check_result
    log_server.logging('>>>>>>>> Time of the whole process: {:.6f}'.format(pre_end - pre_start))
    log_server.logging('============Exit Checker System !===========')
    return jsonify(result)

if __name__ == '__main__':
    # app.run(host='0.0.0.0', port="10010")
    #app.run(host='0.0.0.0', port="9779")
    app.run()
