#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author : yqw
# @Time: 2020-11-23
# @Function: 中文检错器


import re
import time
import json
from zh_utils import SYM_MAP, FW_ALPHABET,ALPHABET_DICT,SYM_SIM,PUNCTUATION
from zh_utils import bracket, qa_matching, serial_matching,simple_serial_matching, preprocess, \
    split_sentence, pump_list, pump_list_to_str,checkSymbol, latex_process, show_text_value, sortList
from zh_process import Data_Process
from zh_ContMatch import AQCMatch
from zh_config import zh_check_config
from logserver import log_server



class ZhCheck(object):
    """ 中文检查类 """
    def __init__(self, dictionary, subject, lac, faspell=None, ancient=None, word2vec=None):
        self.lac_mode = lac
        self.position = {}
        self.errorList = {}
        self.id = dictionary['_id']
        self.description = dictionary['description']
        self.answer = dictionary['answers']
        self.solution = dictionary['solutions']
        self.stems = dictionary['stems']
        self.type = dictionary['type']
        self.subject = subject
        self.config = zh_check_config
        # model loading...
        # modified
        self.spellchecker = faspell
        self.ancient = ancient
        self.word2vec = word2vec
        self.process = Data_Process(self.subject)
        self.aqc = AQCMatch(self.lac_mode, self.description, self.answer, self.solution, self.stems, self.subject)


    def addError(self, index, errorType, description, source, target, position, replace,_list):
        """
        添加错误
        """
        error_detail = {}
        error_detail['_id'] = index
        error_detail['error_type'] = zh_check_config['error_type'][errorType]
        error_detail['description'] = description
        error_detail['source'] = source
        error_detail['target'] = target
        error_detail['position'] = position
        error_detail['replace'] = replace
        _list.append(error_detail)
        return _list


    def adderrorList(self, error, sent, replace = 0, description = None,source = None, target = None, pos = None):
        """
        错误类型储存格式为：
        {tid:['error_sent':sent, 'error_detail':[
        {'error_type': type, 'description':description},
        {'error_type': type, 'description':description},
        ...
        ]]}
        """
        # 如果错误存储信息列表中，已经存储相同ID 的错误信息， 则往此ID 中添加详细的错误信息
        errorType = {}
        flag = False
        if self.id in self.errorList:
            # 如果错误类型里已经有相同的错误句子， 则直接往里面添加错误详细信息
            _length = len(self.errorList[self.id])
            for errs in range(0, _length):
                if sent == self.errorList[self.id][errs]['error_sent']:
                    _list = self.errorList[self.id][errs]['error_detail']
                    index = len(_list)
                    _list = self.addError(index+1, error, description,source, target, pos, replace, _list)
                    self.errorList[self.id][errs]['error_detail'] = _list
                    flag=True
            # 否则， 添加错误句子，并添加此句子的错误详细信息
            if not flag:
                errorType['error_sent'] = sent
                _list = []

                _list = self.addError(1, error, description,source, target, pos, replace, _list)
                errorType['error_detail'] = _list
                self.errorList[self.id].append(errorType)

        # 否则， 添加错题ID， 此错题ID 的错误句子， 与此句子的所有详细错误信息
        else:
            _errlist = []
            errorType['error_sent'] = sent
            _list = []
            _list = self.addError(1, error, description,source, target, pos, replace, _list)
            errorType['error_detail'] = _list
            _errlist.append(errorType)
            self.errorList[self.id] = _errlist


    def delTab(self, text):
        """
        去除制表符， 换行符, 去除两个以上的英文字符
        """
        log_server.logging(">>> Checking zh deltab error !")
        start = time.time()
        sentence = re.sub(r'[\t\n\xa0\s]', '', text)
        sentence = re.sub(r'[a-zA-Z]{2,}','', sentence)
        log_server.logging("Deltab finish! Total time is {} >>>".format(time.time()-start))
        return sentence


    def extractLatex(self, text):
        """
        提取Latext公式， 并记录位置。
        """

        log_server.logging(">>> Extrace Latex !")
        start = time.time()
        latex = re.findall(r'\$.+?\$', text)
        alphabet = re.findall(r'(\$\{\s*[A-F]{1,4}\s*\}\$)',text)
        alphabet1 = re.findall(r'(\$\{\s*(\\times)\s*\}\$)', text)
        diff = set(latex).difference(set(alphabet + alphabet1))
        idx = list()  # index of list
        for value in diff:
            # will return the index of the latex formula in the sentence
            # 找到题干中latex公式的位置， 并保存
            index = text.find(value)
            while index != -1:

                latex_index = {}
                latex_index['id'] = self.id
                latex_index["sources"] = text
                latex_index["index"] = index

                # 如若此latext公式已经存在在列表中， 则直接往对应的LaTeX公式中保存句子位置等信息
                if value in self.position.keys():
                    self.position[value].append(latex_index)

                # 如若此latext公式尚未存在在列表中， 则添加相对应的所有位置信息。
                else:
                    idx.append(latex_index)
                    self.position[value] = idx

                # 继续寻找该句子中下一latex公式的位置
                index = text.find(value, index + 1)

            #返回题干中，用空格代替LaTeX公式。
            text = text.replace(value, len(value)*'&')
        # print('extract latex {}'.format(time.time() - start))
        log_server.logging("Extrace Latex finish! Total time is {} >>>".format(time.time() - start))
        return text


    def final_check_confusion_symbol(self):
        """
        优化终检问题，解决多个符号乱用
        eg:
        。，|。,|!。
        :return:
        """
        log_server.logging(">>> Check confusion symbol !! <<<<")
        start = time.time()
        check_list = [(self.description, 'description'), (self.stems, 'stems'), (self.solution,'solutions')]
        
        for value in check_list:
            if isinstance(value[0], str) and len(value[0])>0 and value[0] is not None:
                errors_list, result_list = self.process.specialSymbol(value[0], -1)
                if len(errors_list)>0 and len(result_list)>0:
                    self.adderrorList('zh_symbol_error_1', value[1], replace=0,
                                      description=zh_check_config['description']['zh_symbol_error_1'],
                                      source=errors_list, pos=result_list)
            elif isinstance(value[0], list):
                errors_list, result_list = [], []
                for i, data in enumerate(value[0]):
                    if isinstance(data, dict):
                        e, r = self.process.specialSymbol(data['stem'], i)
                        errors_list+=e
                        result_list+=r
                    else:
                        e, r = self.process.specialSymbol(data, i)
                        errors_list += e
                        result_list += r
                if len(errors_list)>0 and len(result_list)>0:
                    self.adderrorList('zh_symbol_error_1', value[1], replace=0,
                                      description=zh_check_config['description']['zh_symbol_error_1'],
                                      source=errors_list, pos=result_list)
        

        # print('confusion Symbol {}'.format(time.time() - start))
        log_server.logging(">>> Finished confusion symbol !! Total time is {} <<<<".format(time.time() - start ))

    def final_check_space_in_solutions(self):
        """
        检查解答中的空格, 开头和结尾的空格不算
        带公式的数学、化学较多，暂时不支持数学、化学
        :return:z
        """
        log_server.logging('>>>>>>Checking extra space in solution<<<<<<')
        start = time.time()
        result_list = []
        for i, text in enumerate(self.solution):
            htmlPattern = re.compile(r'(html\s*{.*}\s*)')
            if len(re.findall(htmlPattern, text)) > 0:
                text = re.sub(htmlPattern, '', text).strip()

            if self.subject not in ['数学', '化学']:
                latex_p = re.compile(r"(\${.*?}\$)")
                space_p = re.compile(r'(?<=\S) {3,}(?=\S)')
                if len(re.findall(latex_p, text)) != 0:
                    for latex in re.findall(latex_p, text):
                        l_len = len(latex)
                        text = text.replace(latex, l_len * '#')
                res = [(m.start(), m.start() + len(m.group())) for m in re.finditer(space_p, text)]
                _, ress = sortList(res, None)
                result_list += [[i, res] for res in ress]
        if len(result_list)>0:
            self.adderrorList('zh_format_error', 'solutions', replace=0,
                  description=zh_check_config['description']['zh_format_error']
                  )
        # print('space checking {}'.format(time.time() - start))
        log_server.logging(">>> Finished space checking! Total time is {}.<<< ".format(time.time() - start))


    def matchbracket(self):
        """
        检测括号，引号是否匹配
        """
        log_server.logging(">>> Checking Bracket <<<")
        start = time.time()
        check_list = [(self.description, 'description'),(self.stems, 'stems'), (self.solution,'solutions')]


        for value in check_list:
            symbol, position = [], []
            if isinstance(value[0], list):
                for i, text in enumerate(value[0]):
                    if isinstance(text, dict):
                        s, p = self.process.bracketMatch(text['stem'], i)
                        symbol += s
                        position += p
                    else:
                        s, p = self.process.bracketMatch(text, i)
                        symbol +=s
                        position +=p
                if len(symbol)>0 and len(position) >0:
                    self.adderrorList('zh_symbol_error', sent=value[1], replace=0,
                                  description=zh_check_config['description']['zh_symbol_error'],
                                  source=symbol,
                                  pos=position)
            else:
                if len(value[0]) > 0:
                    s, p = self.process.bracketMatch(value[0], -1)
                    if len(s)>0 and len(p)>0:
                        self.adderrorList('zh_symbol_error',sent=value[1],replace=0,
                                          description=zh_check_config['description']['zh_symbol_error'],
                                          source=s,
                                          pos=p)
        # print('bracket checking  {}'.format(time.time() - start))
        log_server.logging('>>> Finished bracket checking!! Total time is {}<<<'.format(time.time() - start))


    def enSymbolCheck(self):
        """
        对题目， 解答还有选项进行全半角英文字符混用检测。
        如果检测到混用的情况， 返回检测错误。并且将全角英文字符更改会半角英文字符。
        :param enSymbolDetect:
        :return:
        """
        log_server.logging(">>> Checking english symbol in sentence!!! <<<")
        start = time.time()
        check_list = [(self.description, "description"), (self.solution,"solutions")]
        count= 0

        for _list in check_list:
            record, replaces, positions = [], [], []
            sentence = _list[0]
            type = _list[1]
            cont = ''
            if all(sentence):
                if isinstance(sentence, list):
                    for i, sent in enumerate(sentence):
                        if isinstance(sent, dict):
                            flag, r, repl, pos = self.process.enSymbolProcess(i, sent['stem'])
                        else:
                            flag, r, repl, pos = self.process.enSymbolProcess(i, sent)
                        if flag:
                            record+=r
                            replaces +=repl
                            positions +=pos
                    if len(record)>0 and len(replaces)>0 and len(positions)>0:
                        count += 1
                        self.adderrorList('zh_enSymbol_unmatch_error', sent=type, replace=1,
                                          description=zh_check_config['description']['zh_enSymbol_unmatch_error'].format(type),
                                          source=record,
                                          target=replaces,
                                          pos=positions
                                          )
                else:
                    flag, r, repl, pos = self.process.enSymbolProcess(-1, sentence)
                    if flag:
                        record += r
                        replaces += repl
                        positions += pos
                    if len(record)>0 and len(replaces)>0 and len(positions)>0:
                        count+=1
                        self.adderrorList('zh_enSymbol_unmatch_error',sent = type, replace=1,
                                          description=zh_check_config['description']['zh_enSymbol_unmatch_error'].format(type),
                                          source=record,
                                          target = replaces,
                                          pos = positions
                                    )
        # print('english symbol checking {}'.format(time.time() - start))
        log_server.logging(">>> Finished English symbol checking!!! Total time is {}<<<".format(time.time() - start))
        if count==0:
            return True
        else:
            return False


    def serial_check(self, serialCheck):
        """
        对答案和解答中是否存在某小题号缺失， 小题号格式不完整， 小题号格式不统一等情况进行检测。
        题目格式比较多样， 有（一）/一、/Ⅰ/①/（1）/(1)等格式存在。 但是我们只对（1）/(1)进行检验。
        如果某小题中，缺失小题号， 但是它为选择题选项， 则跳过。
        :param serialCheck:
        :return:
        """
        if serialCheck:
            log_server.logging('>>> Checking serial sub question !!! <<<')
            start = time.time()
            flag = False
            checkList = [(self.stems, 'stems'), (self.answer, 'answers'),(self.solution,'solutions')]
            if self.type == '选择题':
                flag = True
            if not flag:
                for checkL in checkList:
                    text = pump_list_to_str(checkL[0])
                    if simple_serial_matching(text):
                        zh_pattern = re.findall(r'([\(\（][一二三四五六七八九十][\)\）]{1,2})', text)
                        zh_pattern1 = re.findall(r'([一二三四五六七八九十]{1,2}、)', text)
                        zh_pattern2 = re.findall(r'([ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]{1,3})', text)
                        zh_pattern3 = re.findall(r'(【[\u4e00-\u9fff]+】)', text)
                        if (len(zh_pattern)==0) & (len(zh_pattern1)==0) & (len(zh_pattern2)==0) &(len(zh_pattern3)==0):
                            if len(checkL[0]) > 1:
                                for i, value in enumerate(checkL[0]):
                                    if isinstance(value, dict):
                                        value = pump_list_to_str(value['stem'])
                                    else:
                                        value = pump_list_to_str(value).strip()
                                    special = re.search(r'^(【拓展】)', value)

                                    if (special is not None) :
                                        pass
                                    else:
                                        pattern = re.search(r'^(解[：:])', value)
                                        if pattern is not None:
                                            value = re.sub(r'(解[：:])', '', value).strip()
                                        pattern1 = re.search(r'^([\(\（](\${\d+\}\$)[\)\）])', value)
                                        pattern2 = re.search(r'^(\$\{[\(\（]\d+[\)\）]\}\$)', value)
                                        if (pattern1 is not None) | (pattern2 is not None):
                                            value = re.sub(r'[\$\{\}\$]', '', value).strip()

                                        x = re.search(r'^([\（\(](\d){1,2}[\）\)])', value)
                                        x1 = re.search(r'([\（\(](\d){1,2}[\）\)])', value)
                                        x2 = re.search(r'^((\d){1,2}\.)', value)

                                        if (x2 == None):
                                            if (x == None) & (x1 == None):

                                                if len(value)<=10:
                                                        if len(re.findall('[A-D]{1,4}', value))>0:
                                                            pass
                                                        else:
                                                            self.adderrorList('zh_serial_unmatch_error',checkL[1],replace=0,
                                                                              description=zh_check_config['description']['zh_serial_unmatch_error'].format(checkL[1], i + 1, i+1))
                                                else:
                                                    self.adderrorList('zh_serial_unmatch_error',checkL[1], replace=0,
                                                              description=zh_check_config['description']['zh_serial_unmatch_error'].format(checkL[1], i + 1, i+1))
                                            else:
                                                pass
                                        else:
                                            pass
                # print('serial sub question checking {}'.format(time.time() - start))
                log_server.logging('>>>Finished serial sub question checking!!! Total time is {}'.format(time.time()-start))
            else:
                pass


    def typeCheck(self, typeMatch):
        """
        对题目进行题型匹配功能检测：
            选择题的选项不能为空
            判断题的答案需匹配到关键字
            除辨析题和以上两个题型外的其他题型，
                如果能匹配到判断题关键字， 则题型不匹配。
                如果选项不为空， 则题型不匹配。
        :param typeMatch: 只有typeMatch==True的时候， 才能添加并显示错误。
        :return:
        """
        log_server.logging(">>> Checking the type match !!!<<<")
        start = time.time()

        answer = pump_list_to_str(self.answer)

        if self.subject == '地理':
            value_list = ['对','错']
        else:
            value_list = None

        if (self.type == '选择题') | (self.type == '多选题') | (self.type == '单选题'):
            flag=False
            for stem in self.stems:
                if "options" in stem.keys():
                    if all(stem['options']):
                        flag= True

            if flag:
                return True
            else:
                if typeMatch:
                    self.adderrorList('zh_type_unmatch_error', sent = 'type', replace = 0,
                                      description=zh_check_config['description']['zh_type_unmatch_error']['选择题'].format(self.type))
                else:
                    return False
        elif self.type == '判断题':
            """
            生物较为特殊， 判断题中是有存在T/F,A/B这种格式的判断。
            如果答案中存在小题号， 那么每个小题都必须有判断题的关键字， 否则提醒不匹配
            """
            if self.subject == '政治':
                return True
            else:
                if value_list is None:
                    value_list = ['T', 'F', 'A','B','对','错']
                else:
                    value_list += ['T', 'F', 'A','B','对','错']
                p1 = re.compile(r'[（\(]\d+[）\)]')
                """检查答案中是否存在小题号"""
                if len(self.answer)>1:
                    count = 0
                    record = []
                    for i,ans in enumerate(self.answer):
                        ans = pump_list_to_str(ans)
                        if simple_serial_matching(answer):
                            ans = re.sub(p1, '', ans)
                        ans = latex_process(ans)
                        if checkSymbol(ans.strip(PUNCTUATION), value_list = value_list):
                            count+=1
                        else:
                            record.append(i+1)
                    if count == len(self.answer):
                        return True
                    else:
                        if typeMatch:
                            self.adderrorList('zh_type_unmatch_error', sent = 'type', replace=0,
                                              description=zh_check_config['description']['zh_type_unmatch_error']['判断题'].format(self.type, record))
                        else:
                            return False
                else:
                    if simple_serial_matching(answer):
                        answer = re.sub(p1, '', answer)
                    answer = latex_process(answer)
                    if checkSymbol(answer.strip(PUNCTUATION), value_list=value_list):
                        return True
                    else:
                        if typeMatch:
                            self.adderrorList('zh_type_unmatch_error', sent='type', replace=0,
                                              description=zh_check_config['description']['zh_type_unmatch_error']['判断题'].format(self.type,[1]))
                        else:
                            return False
        else:
            """
            非判断题的答案中存在A/B可能是为选择题等情况。 因此不添加A/B关键字
            """
            if not (self.subject == '生物'):
                if value_list is None:
                    value_list = ['T', 'F']
                else:
                    value_list += ['T', 'F']
            if self.type == '辨析题':
                return True
            else:
                flag = False
                for stem in self.stems:
                    if "options" in stem.keys():
                        flag=True
                if flag:
                    """
                    语文中的现代文阅读， 文言文阅读， 综合读写等题目中都是选择题+解答题混合的格式， 无法进行准确分辨，因此跳过语文科目。
                    """
                    if (self.subject == '语文'):
                        return True
                    else:
                        if typeMatch:
                            self.adderrorList('zh_type_unmatch_error',sent='type', replace=0,
                                              description=zh_check_config['description']['zh_type_unmatch_error']['非选择题'].format(self.type))
                        else:
                            return False
                else:
                    p1 = re.compile(r'[（\(]\d+[）\)]')
                    if len(self.answer)>1:
                        """
                        当答案中存在小题号的情况， 我们需要判断是否所有小题的内容都为判断题内容。 否则它并非判断题，因此没有题型不匹配错误。
                        """
                        count = 0
                        for ans in self.answer:
                            if isinstance(ans, list):
                                ans = ''.join(ans)
                            if simple_serial_matching(answer):
                                ans = re.sub(p1, '', ans)
                            ans = latex_process(ans)

                            if checkSymbol(ans.strip(PUNCTUATION), value_list=value_list):
                                count += 1

                        if count == len(self.answer):
                            if self.subject == '语文':
                                return True
                            else:
                                if typeMatch:
                                    self.adderrorList('zh_type_unmatch_error',sent = 'type', replace=0,
                                                      description=zh_check_config['description']['zh_type_unmatch_error']['非判断题'].format(self.type))
                                else:
                                    return False
                        else:
                            return True

                    else:
                        if simple_serial_matching(answer):
                            answer = re.sub(p1, '', answer)
                        answer = latex_process(answer)
                        if checkSymbol(answer.strip(PUNCTUATION), value_list =value_list):
                            if self.subject == '语文':
                                return True
                            else:
                                if typeMatch:
                                    self.adderrorList('zh_type_unmatch_error',sent='type', replace=0,
                                                      description=zh_check_config['description']['zh_type_unmatch_error']['非判断题'].format(self.type))
                                else:
                                    return False
                        else:
                            return True

        log_server.logging(">>>  Type Match finish! Total time is {} <<<".format(time.time() - start))


    def contTypeCheck(self, contTypeMatch):
        """
        对题目的格式进行校验。
        判断题的关键字， 除了√×w外， 其他一律不规范
        选择题中答案如果不是A-Z， 一律视为不规范。
        :param contTypeMatch:
        :return:
        """
        def judgeCheck(answer, contTypeMatch):
            if self.subject == '政治':
                return True
            elif (self.subject == '地理'):
                if answer.strip(PUNCTUATION) in ['对', '错']:
                    return True
                else:
                    if contTypeMatch:
                        self.adderrorList('zh_type_style_unmatch_error', sent='type', replace=0,
                                          description=zh_check_config['description']['zh_type_style_unmatch_error'][
                                              '判断题'].format(self.type))
                    else:
                        return False
            elif (self.subject == '生物'):
                if answer.strip(PUNCTUATION) in ['T', 'F']:
                    return True
                else:
                    if contTypeMatch:
                        self.adderrorList('zh_type_style_unmatch_error', sent='type', replace=0,
                                          description=zh_check_config['description']['zh_type_style_unmatch_error'][
                                              '判断题'].format(self.type))
                    else:
                        return False
            else:
                if contTypeMatch:
                    self.adderrorList('zh_type_style_unmatch_error', sent='type', replace=0,
                                      description=zh_check_config['description']['zh_type_style_unmatch_error'][
                                          '判断题'].format(self.type))
                else:
                    return False

        log_server.logging(">>> Checking the format of the question! <<<")
        start = time.time()
        pattern = re.compile(r'[A-Za-z]')
        answer = pump_list_to_str(self.answer)

        if not simple_serial_matching(answer):
            if not all(self.solution):
                if contTypeMatch:
                    self.adderrorList('zh_type_style_unmatch_error',sent='type', replace=0,
                                      description=zh_check_config['description']['zh_type_style_unmatch_error']['选择题']['解答'],source='解答：{}'.format("text"))
                else:
                    return False
            if self.type == '判断题':
                if len(answer)>1:
                    for ans in answer:
                        if isinstance(ans, list):
                            ans = ''.join(ans)
                        ans = latex_process(ans)
                        if checkSymbol(ans.strip(PUNCTUATION), special = True):
                            return True
                        else:
                            return judgeCheck(answer, contTypeMatch)
                else:
                    answer = latex_process(answer)
                    if checkSymbol(answer.strip(PUNCTUATION), special = True):
                        return True
                    else:
                        return judgeCheck(answer, contTypeMatch)

            elif (self.type == '选择题') | (self.type =='多选题') | (self.type == '单选题'):
                if len(re.findall(pattern, answer))>0:
                    return True
                else:
                    if contTypeMatch:
                        self.adderrorList('zh_type_style_unmatch_error',sent='type', replace=0,
                                          description=zh_check_config['description']['zh_type_style_unmatch_error']['选择题']['答案'].format(self.type))
                    else:
                        return False
            else:
                return True
        else:
            return True

        log_server.logging(">>> Format checking finished! Total time is {} <<<".format(time.time() - start))


    def spellDetect(self, tradWord, wrongWord):
        """
        错词检测：繁体字检测， 错别字检测
        """
        log_server.logging(">>> Detecting wrong words! <<<")
        start = time.time()

        """理科的解答多为公式， 因此不对理科的解答做错词检测"""
        if self.subject not in ['物理', '化学', '数学']:
            totallist = [(self.description, 'description') , (self.stems, 'stems'), (self.solution,'solutions')]
        else:
            totallist = [(self.description, 'description'), (self.stems,'stems')]

        if tradWord | wrongWord:
            for value in totallist:
                source = []
                target = []
                position = []
                trad_list = []
                if isinstance(value[0], str) and all(value[0]):
                    if wrongWord:
                        try:
                            trad_list, source, target, position = self.process.spell_process(value[0], -1, self.ancient, self.spellchecker, self.description, tradWord)
                        except Exception as e:
                            log_server.logging('>>>Checking spell function exception: {}'.format(e))
                    elif tradWord:
                        try:
                            trad_list += self.process.tradProcess(value[0], -1)
                        except Exception as e:
                            log_server.logging('>>>Checking trad function exception: {}'.format(e))


                else:
                    if all(value[0]):
                        for i, text in enumerate(value[0]):
                            if isinstance(text, dict):
                                if wrongWord:
                                    try:
                                        tradl, s, t, p = self.process.spell_process(text['stem'], i,self.ancient,self.spellchecker,self.stems[i]['stem'], tradWord)
                                        source+=s
                                        target+=t
                                        position+=p
                                        trad_list +=tradl
                                    except Exception as e:
                                        log_server.logging('>>>Checking spell function exception: {}'.format(e))

                                elif tradWord:
                                    try:
                                        trad_list += self.process.tradProcess(text['stem'], i)
                                    except Exception as e:
                                        log_server.logging('>>>Checking trad function exception: {}'.format(e))
                            else:
                                if wrongWord:
                                    try:
                                        tradl, s, t, p = self.process.spell_process(text, i,self.ancient,self.spellchecker,self.solution[i], tradWord)
                                        source += s
                                        target += t
                                        position += p
                                        trad_list += tradl
                                    except Exception as e:
                                        log_server.logging('>>>Checking spell function exception: {}'.format(e))
                                else:
                                    try:
                                        trad_list += self.process.tradProcess(text, i)
                                    except Exception as e:
                                        log_server.logging('>>>Checking trad function exception: {}'.format(e))

                    else:
                        pass

                if source and target and position:
                    self.adderrorList('zh_spell_error', sent=value[1], replace=1,
                                      description=zh_check_config['description']['zh_spell_error'].format(
                                          value[0]),
                                      source=source,
                                      target=target,
                                      pos=position)

                if tradWord and (trad_list is not None):
                    if len(trad_list) > 0:
                        source, target, position = [],[],[]
                        for trad in trad_list:
                            source.append(trad[0])
                            target.append(trad[1])
                            position.append([trad[3], (trad[2], trad[2] + 1)])
                        self.adderrorList('zh_font_error', sent=value[1], replace=1,
                                          description=zh_check_config['description'][
                                              'zh_font_error'].format(
                                              value[0]),
                                          source=source, target=target, pos=position)


        log_server.logging(">>>  Wrong words detection finish! Total time is {} <<<".format(time.time() - start))


    def multiChoice(self):
        """
        此为选择题: 答案A与故选A校验
        """
        errorAns = self.aqc.answerMatch()
        if errorAns is not None:
            for err in errorAns:
                self.adderrorList(err[1], 'answers-solutions', replace=0, description=err[0]+'; 大概位置为：'+str(err[2]))
        return errorAns


    def shortAns(self):
        """
        此为材料分析题，简答题等进行（1）答案与解答校验，（2）题干与解答校验
        """
        errorAns = self.aqc.ansMatch(self.answer, self.question)
        if errorAns is not None:
            for errA in errorAns:
                self.adderrorList(errA[1], 'answers-solutions', replace=0, description=errA[0])


    def ansContMatch(self):
        if (self.subject == '数学') | (self.subject == '政治') | (self.subject == '历史') | (
                self.subject == '语文') | (self.subject == '生物'):
            pass
        else:
            errorCont = self.aqc.ansContMatch()
            if errorCont is not None:
                for errC in errorCont:
                    self.adderrorList(errC[1], 'answers-solutions', replace =0, description = errC[0])


    def contentMatch(self, keywordMatch, contentMatch):
        """
        分题型对题干， 答案，选项， 解答进行匹配。
        选择题：
            数学， 政治，历史，语文的只做：答案A与解答故A校验
            其他科目则，答案A与解答故A校验 和 题干+正确答案选项 -> 解答校验。
        简答题， 材料分析题， 填空题， 解答题， 实验探究他， 选择填空题，论述题等：
            数学：pass
            其他科目则：答案与解答校验 和题干与解答校验
        """
        log_server.logging(">>> Checking zh keywords match error !")
        start = time.time()


        if (self.type == '选择题') | (self.type == '多选题') | (self.type=='单选题'):
            """
                选择题或多选题， 数学，政治，历史与语文只做答案A 与故选A 校验
                其他科目则做答案A 与故选A校验 和 题干加选项与解答校验。
            """
            if keywordMatch:
                errorAns = self.multiChoice()
                if (errorAns is None) & contentMatch:
                    self.ansContMatch()
            elif contentMatch:
                self.ansContMatch()

        elif (self.type == '材料分析题') | (self.type == '简答题') | (self.type == '实验探究题') | (self.type == '论述题') | (
                self.type == '选择填空题')|(self.type == '解答题') | (self.type == '填空题'):
            """
                解答题，填空题，等， 数学跳过
                其他科目则做答案与解答校验， 和题干与解答校验。
            """
            if contentMatch:
                if (self.subject == '数学'):
                    pass
                else:
                    self.shortAns()

        elif (self.type == '判断题'):
            if keywordMatch:
                """
                因为地理学科的解答多没有明确提及判断正确或错误字眼， 因此地理学科跳过。
                因为政治的判断题中的解答多为开放性回答， 并没有具体提及判断正确或错误的字眼。
                """
                if (self.subject == '地理') : #& (self.subject == '政治')
                    pass
                else:
                    result = qa_matching(self.answer, self.solution, subject = self.subject)
                    if result is not None:
                        if len(result) > 0:
                            if result['description'] != 'solution匹配不到关键字':
                                self.adderrorList(result['errorType'], sent = 'answers-solutions', replace=0, description=result['description'])

        elif(self.type == '辨析题'):
            if checkSymbol(self.answer):
                if keywordMatch:
                    result = qa_matching(self.answer, self.solution,subject = self.subject)
                    if (result is not None):
                        if len(result) > 0:
                            if result['description'] != 'solution匹配不到关键字':
                                self.adderrorList(result['errorType'], sent = 'answers-solutions', replace=0, description=result['description'])
            else:
                if contentMatch:
                    errorAns = self.aqc.ansMatch(self.answer, self.question)
                    if (errorAns is not None):
                        for errA in errorAns:
                            self.adderrorList(errA[1], sent='answers-solutions', replace=0, description=errA[0])

        log_server.logging("Keywords match finish! Total time is {} >>>".format(time.time() - start))


    def __call__(self,  tradWordDetect = False, wrongWordDetect = False,  keywordMatch=False, contentMatch=False,
                 symbolCheck=False, typeMatch=False, contTypeMatch = False, enSymbolDetect= False, serialCheck = False):

        log_server.logging(">>> Enter zh_checker ! ")
        try:
            if symbolCheck:
                self.final_check_confusion_symbol()
                self.final_check_space_in_solutions()
        except Exception as e:
            log_server.logging('>>>Checking special symbol function exception: {}'.format(e))
        
        try:
            if serialCheck:
                self.serial_check(serialCheck)
        except Exception as e:
            log_server.logging('>>>Checking serial function exception: {}'.format(e))
        
        
        self.description = self.delTab(self.description)
        self.description = self.extractLatex(self.description)
        solu_list =[]
        for solu in self.solution:
            solu_list.append(self.extractLatex(solu))
        self.solution = solu_list
        
        try:
            if symbolCheck:
                self.matchbracket()
        except Exception as e:
            log_server.logging('>>>Checking symbol function exception: {}'.format(e))
        
        try:
            if enSymbolDetect:
                self.enSymbolCheck()
        except Exception as e:
            log_server.logging('>>>Checking enSymbol function exception: {}'.format(e))
        
        try:
            if self.typeCheck(typeMatch):
                if self.contTypeCheck(contTypeMatch):
                    self.contentMatch(keywordMatch, contentMatch)
        except Exception as e:
            log_server.logging('>>>Checking type function exception: {}'.format(e))
        
        
        try:
            #错词功能部分。 测试时
            if self.subject == '语文':
                if self.type in ['现代文阅读', '写作', '名著阅读']:
                    self.spellDetect(tradWordDetect, wrongWordDetect)
                else:
                    pass
            elif self.subject in ['化学', '数学', '地理']:
                pass
            else:
                self.spellDetect(tradWordDetect, wrongWordDetect)
        except Exception as e:
            log_server.logging('>>>Checking spell and trad function exception: {}'.format(e))
        log_server.logging("Zh_checker finish ! >>>")

        return self.position, self.errorList

