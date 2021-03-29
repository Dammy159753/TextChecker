#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# @File    :   check_match.py
# @Time    :   2020/11/13
# @Author  :   dyu

import re
import json
import Levenshtein
from collections import Counter
from en_utils import get_recursively_list, get_answers, parse_data, get_common_str, make_dict, order_list

class MatchChecker:
    '''
    答案-解答对应质检
    '''
    def process_latin(self, alphabet_list):
        '''
        全半角统一转换成半角
        '''
        alphabet_dict = {'Ａ':'A', 'Ｂ':'B', 'Ｃ':'C','Ｄ':'D', 'Ｅ':'E', 'Ｆ':'F', 'Ｇ':'G', 'Ｈ':'H', 'Ｉ':'I', 'Ｊ':'J',
                        'Ｋ':'K', 'Ｌ':'L', 'Ｍ':'M', 'Ｎ':'N', 'Ｏ':'O', 'Ｐ':'P', 'Ｑ':'Q', 'Ｒ':'R', 'Ｓ':'S', 'Ｔ':'T',
                        'Ｕ':'U', 'Ｖ':'V', 'Ｗ':'W', 'Ｘ':'X', 'Ｙ':'Y', 'Ｚ':'Z'}
        for i in range(len(alphabet_list)):
            if isinstance(alphabet_list[i],str):
                if alphabet_list[i] in alphabet_dict.keys():
                    alphabet_list[i] = alphabet_dict[alphabet_list[i]]
            elif isinstance(alphabet_list[i],list):
                alphabet_list[i] = self.process_latin(alphabet_list[i])
        return alphabet_list

    def append_to_json(self, data, file):
        '''
        Append en_data to json file
        将数据以append的形式加入json文件
        '''
        with open(file,'a') as af:
            json_str = json.dumps(data, ensure_ascii=False)
            af.write(json_str)

    def key_word_matching(self, string):
        '''
        Match pattern in the text according to keywords
        按关键词匹配文本中的pattern
        '''
        key_words = ['答案为','选项为','选','填','选择','选：','选:']
        for word in key_words:
            p=re.compile(r"{}([A-Z])".format(word))
            res3 = p.search(string)
            if res3 is not None:
                break
        return res3

    def compare(self, list1, list2):
        '''
        Compare two lists and return the indexs of different components
        对比两个列表并返回不相同的元素对应的索引
        '''
        error_index = []
        for i in range(0, len(list1)):
            if list1[i] != list2[i]:
                i += 1
                error_index.append(i)
        return error_index

    def process_answer(self, answer_list):
        '''
        Remove special symbols of the answer
        去除文本中的特殊字符
        '''
        for i in range(len(answer_list)):
            if isinstance(answer_list[i],str):
                
                answer_list[i] = re.sub(r'\n|[_]+','',answer_list[i])
                answer_list[i] = re.sub(r'\xa0',' ',answer_list[i])
                answer_list[i] = re.sub(r"．",'.',answer_list[i])
                answer_list[i] = re.sub(r'[（|(][ ]*[\d]+[ ]*[)|）]|[①②③④⑤⑥⑦⑧⑨]','',answer_list[i])
                answer_list[i] = answer_list[i].strip()
            elif isinstance(answer_list[i],list):
                processed_list = list()
                for ans in answer_list[i]:
                    ans = re.sub(r'\n|[_]+','',ans)
                    ans = re.sub(r'\xa0',' ',ans)
                    ans = re.sub(r"．",'.',ans)
                    ans = re.sub(r'[（|(][ ]*[\d]+[ ]*[)|）]|[①②③④⑤⑥⑦⑧⑨]','',ans)
                    processed_list.append(ans)
                answer_list[i] = processed_list
        return answer_list

    def getCommonStr(self, str1, str2):
        '''
        Obtain the maximum common string between two strings
        获取两个字符串的最大公共子字符串的长度
        '''
        lstr1 = len(str1)
        lstr2 = len(str2)
        record = [[0 for i in range(lstr2 + 1)] for j in range(lstr1 + 1)]  # 多一位
        maxNum = 0  # 最长匹配长度
        # p = 0  # 匹配的起始位
        for i in range(lstr1):
            for j in range(lstr2):
                if str1[i] == str2[j]:
                    # 相同则累加
                    record[i + 1][j + 1] = record[i][j] + 1
                    if record[i + 1][j + 1] > maxNum:
                        # 获取最大匹配长度
                        maxNum = record[i + 1][j + 1]
                        # 记录最大匹配长度的终止位置
                        # p = i + 1
        return maxNum


    # 2020.12.7更新代码
    def matching_1(self, answers, solutions, result_dict=None):
        '''
        匹配模式1
        对选择题answer与solution是否对应进行质检
        增加对多选题的校验
        '''
        if result_dict is None:
            result_dict = dict()
        answer_list = get_answers(answers)
        answer_list = self.process_answer(answer_list)
        answer_list = self.process_latin(answer_list)
        solution_ans = list()
        scheme_error_list = list()
        # answer格式校验
        for index,ans in enumerate(answer_list):
            if isinstance(ans,str):
                if ans.isupper() == False:
                    scheme_error_list.append(index+1)
            elif isinstance(ans,list):
                for a in ans:
                    if a.isupper() == False:
                        scheme_error_list.append(index+1)
                        break
        if scheme_error_list:
            result_dict["flag"] = False
            result_dict['error_sent'] = 'type'
            result_dict['error_type'] = '题型/答案格式错误'
            result_dict['description'] = '格式错误：答案{}格式错误'.format(scheme_error_list)
            return result_dict
            
        if len(solutions) == len(answer_list):
            for index,s in enumerate(solutions):
                if len(answer_list[index]) == 1:
                    s = re.sub(r'^[ ]+|\n','',s)
                    s = re.sub(r'\xa0',' ', s)
                    s_list = self.process_latin(list(s))
                    s = ''.join(s_list)
                    s = s.strip()
                    res1 = re.search(r'^[A-Z]', s)
                    if res1 is not None:
                        solution_ans.append(res1[0])
                    elif res1 is None:
                        res2 = re.search(r'[(|（][ ]*\d+[ ]*[）|)][\s]*([A-Z])', s)
                        if res2 is not None:
                            solution_ans.append(res2[1])
                        elif res2 is None:
                            res3 = self.key_word_matching(s)
                            if res3 is not None:
                                solution_ans.append(res3[1])
                            else:
                                solution_ans.append('')
                            # else:
                            #     return True
                elif len(answer_list[index]) > 1:
                    s_list = self.process_latin(list(s))
                    s = ''.join(s_list)
                    s = s.strip()
                    res = re.search(r'^[(|（][ ]*\d+[ ]*[）|)][\s]*([A-Z])[\s]*[/][\s]*([A-Z])', s)
                    if res:
                        res = self.process_answer([res[0]])
                        res = str(res[0])
                        solution_ans.append(res.split("/"))
                    elif not res:
                        res = re.search(r'^[\s]*([A-Z])[\s]*[/][\s]*([A-Z])', s)
                        if res:
                            res = self.process_answer([res[0]])
                            res = str(res[0])
                            solution_ans.append(res.split("/"))
                        elif not res:
                            res = re.findall(r'[(|（][ ]*\d+[ ]*[）|)][\s]*([A-Z])', s)
                            if res:
                                solution_ans.append(res)
                            else:
                                solution_ans.append("")
        elif len(solutions) == 1:
            s_list = self.process_latin(list(solutions[0]))
            s = ''.join(s_list)
            s = s.strip()
            solution_ans = re.findall(r'[(|（][ ]*\d+[ ]*[）|)][\s]*([A-Z])', s)
            if not solution_ans:
                res = re.search(r'^[\s]*([A-Z])[\s]*[/][\s]*([A-Z])', s)
                if res:
                    solution_ans = res[0].split("/")
        
        elif len(solutions) != 1 and len(solutions) != len(answer_list):
            result_dict['flag'] = False
            result_dict['error_sent'] = 'answers-solutions'
            result_dict['error_type'] = '答案-解答小题数不一致错误'
            result_dict['description'] = '答案-解答不匹配错误：答案与解答小题数量不一致'
            return result_dict

        if answer_list == solution_ans:
            result_dict['flag'] = True
            return result_dict
        else:
            result_dict['flag'] = False
            if len(answer_list) != len(solution_ans):
                result_dict['error_sent'] = 'answers-solutions'
                result_dict['error_type'] = '答案-解答小题数不一致错误'
                result_dict['description'] = '答案-解答不匹配错误：答案与解答小题数量不匹配'
                return result_dict
            else:
                error_index = self.compare(answer_list, solution_ans)
                result_dict['error_sent'] = 'answers-solutions'
                result_dict['error_type'] = '答案-解答不匹配错误'
                result_dict['description'] = '答案-解答不匹配错误：答案{}与解答不匹配'.format(str(error_index))
                return result_dict

        return result_dict


    # 2020.12.10更新代码
    def matching_2(self, answers, solution, result_dict=None):
        '''
        匹配模式2
        对填空题answer与solution是否对应进行质检
        '''
        if result_dict is None:
            result_dict = dict()
        answer_list = get_answers(answers)
        answer_list = self.process_answer(answer_list)
        if len(answer_list) == len(solution):
            error_index = list()
            for index,ans in enumerate(answer_list):
                s = solution[index]
                s = re.sub(r"\xa0",' ',s)
                s = re.sub(r"\n",'',s)
                s = re.sub(r"．",'.',s)
                s = re.sub(r'[（|(][ ]*[\d]+[ ]*[)|）]','',s) # 去序号
                s = s.strip()
                if isinstance(ans,str) and len(ans) == 1:
                    # 答案只有一个字母的按选择题匹配
                    s = re.sub(r"\n",'',s)
                    res = re.search(r'^[\S]', s)
                    if res:
                        if ans != res[0]:
                            error_index.append(index+1)
                    else:
                        res2 = re.search(r'[(|（][ ]*\d+[ ]*[）|)][\s]*([a-zA-Z])', s)
                        res3 = re.search(r'[(|（][ ]*\d+[ ]*[）|)][\s]*(\S)', s)
                        if res2 and not res3:
                            if ans != res2[1]:
                                error_index.append(index+1)
                        elif res3 and not res2:
                            if ans != res3[1]:
                                error_index.append(index+1)
                        elif res2 and res3:
                            if ans != res2[0] and res[3]:
                                error_index.append(index+1)
                        else:
                            res4 = self.key_word_matching(s)
                            if res4:
                                if ans != res4[1]:
                                    error_index.append(index+1)
                            else:
                                error_index.append(index+1)
                elif isinstance(ans,str) and len(ans) > 1 and ";" not in ans and "/" not in ans:
                    # 答案长度大于1且小题里没有小题
                    if ans not in s:
                        error_index.append(index+1)
                elif isinstance(ans,str) and len(ans) > 1 and ";" in ans:
                    # 答案长度大于1且小题里有用;分开的小题"a;b;c"
                    sub_list = ans.split(";")
                    for sub_ans in sub_list:
                        sub_ans = sub_ans.strip()
                        if sub_ans not in s:
                            error_index.append(index+1)
                            break
                elif isinstance(ans,str) and len(ans) > 1 and "/" in ans:
                    # 答案长度大于1且小题里有用“/”分开的小题"a/b/c"
                    sub_list = ans.split("/")
                    for sub_ans in sub_list:
                        sub_ans = sub_ans.strip()
                        if sub_ans not in s:
                            error_index.append(index+1)
                            break
                elif isinstance(ans,list):
                    # 小题中有小题的情况["a","b"]
                    for a in ans:
                        if a not in s:
                            error_index.append(index+1)
                            break
            if error_index:
                result_dict["flag"] = False
                result_dict['error_sent'] = 'answers-solutions'
                result_dict["error_type"] = "答案-解答不匹配错误"
                result_dict["description"] = "答案-解答不匹配错误：答案{}与解答不匹配".format(error_index)
                return result_dict
            else:
                result_dict["flag"] = True
                return result_dict
        elif len(answer_list) > 1 and len(solution) == 1:
            # 答案数量大于1，但解答只有一个string，按序号匹配解答内容
            error_index = list()
            s = solution[0]
            s = re.sub(r"\xa0",' ',s)
            s = re.sub(r"．",'.',s)
            for index,ans in enumerate(answer_list):
                if isinstance(ans,str) and len(ans) == 1:
                    # 答案只有一个字母，匹配solution的首字符
                    pattern1 = r'[(|（][ ]*{}[ ]*[）|)][\s]*([a-zA-Z])'.format(index+1)
                    pattern2 = r'[(|（][ ]*{}[ ]*[）|)][\s]*(\S)'.format(index+1)
                    p1 = re.compile(pattern1)
                    p2 = re.compile(pattern2)
                    res1 = re.search(p1,s)
                    res2 = re.search(p2,s)
                    if res1 and not res2:
                        if ans != res[1]:
                            error_index.append(index+1)
                    elif res2 and not res1:
                        if ans != res2[1]:
                            error_index.append(index+1)
                    elif res1 and res2:
                        if ans != res1[1] and ans != res2[1]:
                            error_index.append(index+1)
                    else:
                        error_index.append(index+1)
                elif isinstance(ans,str) and len(ans) > 1 and ";" not in ans and "/" not in ans:
                    # 答案长度大于1且小题里没有小题
                    pattern = r'[(|（][ ]*{}[ ]*[）|)]'.format(index+1)
                    p = re.compile(pattern)
                    res = re.search(p,s)
                    if res:
                        p_index = res.span()[1]-1
                        if ans not in s[p_index:]:
                            error_index.append(index+1)
                    else:
                        error_index.append(index+1)
                elif isinstance(ans,str) and len(ans) > 1 and ";" in ans:
                    # 答案长度大于1且小题里有用;分开的小题"a;b;c"
                    pattern = r'[(|（][ ]*{}[ ]*[）|)]'.format(index+1)
                    p = re.compile(pattern)
                    res = re.search(p,s)
                    if res:
                        p_index = res.span()[1]-1
                        sub_list = ans.split(";")
                        for sub_ans in sub_list:
                            sub_ans = sub_ans.strip()
                            if sub_ans not in s[p_index:]:
                                error_index.append(index+1)
                                break
                    else:
                        error_index.append(index+1)
                elif isinstance(ans,str) and len(ans) > 1 and "/" in ans and ";" not in ans:
                    # 答案长度大于1且小题里有用;分开的小题"a/b/c"
                    pattern = r'[(|（][ ]*{}[ ]*[）|)]'.format(index+1)
                    p = re.compile(pattern)
                    res = re.search(p,s)
                    if res:
                        p_index = res.span()[1]-1
                        sub_list = ans.split("/")
                        for sub_ans in sub_list:
                            sub_ans = sub_ans.strip()
                            if sub_ans not in s[p_index:]:
                                error_index.append(index+1)
                                break
                    else:
                        error_index.append(index+1)   
                elif isinstance(ans,list):
                    # 小题中有小题的情况["a","b"]
                    pattern = r'[(|（][ ]*{}[ ]*[）|)]'.format(index+1)
                    p = re.compile(pattern)
                    res = re.search(p,s)
                    if res:
                        for a in ans:
                            if a not in s[p_index:]:
                                error_index.append(index+1)
                                break
                    else:
                        error_index.append(index+1)         
                else:
                    error_index.append(index+1)
            if error_index:
                result_dict["flag"] = False
                result_dict['error_sent'] = 'answers-solutions'
                result_dict["error_type"] = "答案-解答不匹配错误"
                result_dict["description"] = "答案-解答不匹配错误：答案{}与解答不匹配".format(error_index)
                return result_dict
            else:
                result_dict["flag"] = True
                return result_dict

        else:
            result_dict["flag"] = False
            result_dict['error_sent'] = 'answers-solutions'
            result_dict['error_type'] = '答案-解答小题数不一致错误'
            result_dict['description'] = '答案-解答不匹配错误：答案与解答数量不匹配'
            return result_dict
        return result_dict


    # 2020.12.7更新代码
    def matching_3(self, answer, solution, result_dict=None):
        '''
        匹配模式3
        对短文改错answer与solution是否对应进行质检
        用答案字符串是否被包含在solution中作为判断依据
        '''
        if result_dict is None:
            result_dict = dict()
        if len(answer) == len(solution) == 1 and isinstance(answer[0],str) and isinstance(solution[0],str):
            answer_str = answer[0]
            solution_str = solution[0]
            # answer_list = re.findall(r'[(|（]([\S]+)[)|）]',answer_str)
            answer_list = re.findall(r'[(|（](.+?)[)|）]',answer_str)
            error_list = []
            if answer_list:
                for i in answer_list:
                    i = re.sub(r"\xa0",' ',i)
                    i = i.strip()
                    if i not in solution_str:
                        error_list.append(i)
                if error_list:
                    result_dict['flag'] = False
                    result_dict['error_sent'] = 'answers-solutions'
                    result_dict['error_type'] = '答案-解答不匹配错误'
                    result_dict['description'] = '答案-解答不匹配错误：答案{}与解答不匹配'.format(error_list)
                    return result_dict
                else:
                    result_dict["flag"] = True
                    return result_dict
        elif len(answer) == len(solution) > 1:
            answer = get_recursively_list(answer)
            answer = self.process_answer(answer)
            solution = get_recursively_list(solution)
            solution = self.process_answer(solution)
            ans_match_list = []
            for ans in answer:
                res = re.findall(r'[(|（](.+?)[)|）]',ans)
                if res:
                    sub_ans = list()
                    for r in res:
                        r = re.findall(r"[a-zA-Z' ]+",r)
                        if r:
                            for sub in r:
                                sub = sub.strip()
                                sub_ans.append(sub)
                    ans_match_list.append(sub_ans)
                else:
                    ans_match_list.append('')
            if ans_match_list:
                error_index = []
                for i,ans in enumerate(ans_match_list):
                    for a in ans:
                        if a not in solution[i]:
                            error_index.append(i+1)
                            break
                if len(error_index) > 0:
                    result_dict['flag'] = False
                    result_dict['error_sent'] = 'answers-solutions'
                    result_dict['error_type'] = '答案-解答不匹配错误'
                    result_dict['description'] = '答案-解答不匹配错误：答案{}与解答不匹配'.format(str(error_index))
                    return result_dict
                else:
                    result_dict['flag'] = True
                    return result_dict
        else:
            result_dict['flag'] = False
            if 'error_type' not in result_dict.keys():
                result_dict['error_sent'] = 'type'
                result_dict['error_type'] = '题型/答案格式错误'
                result_dict['description'] = '格式错误：题型或答案格式错误'
            return result_dict
        return result_dict


    def matching_4(self, answer, solution, result_dict=None):
        '''
        匹配模式4
        对书面表达answer与solution是否对应进行质检
        用答案和解答的最大公共子字符串的长度作为判断依据，长度超过30个字符判断为对应，否则不对应
        '''
        if result_dict is None:
            result_dict = dict()
        if len(answer) == len(solution) == 1 and isinstance(answer[0],str) and isinstance(solution[0],str):
            answer = self.process_answer(answer)
            solution = self.process_answer(solution)
            answer_str = answer[0]
            solution_str = solution[0]
            solution_str = re.sub(r'\xa0',' ',solution_str)
            if len(answer_str) > 30:  # 排除answer为“略”的题目
                common_len = self.getCommonStr(answer_str, solution_str)
                # distance = Levenshtein.distance(answer_str,solution_str)
                if common_len > 30:
                    result_dict['flag'] = True
                    return result_dict
                else:
                    result_dict['flag'] = False
                    result_dict['error_sent'] = 'answers-solutions'
                    result_dict['error_type'] = '答案-解答不匹配错误'
                    result_dict['description'] = '答案-解答不匹配错误：答案与解答不匹配'
                    return result_dict
            else:
                result_dict['flag'] = True  # 过短的答案先pass掉
                return result_dict
        else:
            result_dict['flag'] = False
            if 'error_type' not in result_dict.keys():
                result_dict['error_sent'] = 'type'
                result_dict['error_type'] = '题型/答案格式错误'
                result_dict['description'] = '格式错误：题型或答案格式错误'
            return result_dict

        return result_dict


    def parser(self, query, grade_subject):
        """
        解析各类匹配错误
        :param tid:
        :param answers:
        :param solutions:
        :param _type:
        :param grade_subject:
        :return:
        """
        # unmatched_save_file = r'/media/chen2/fxj/Text_Quality_Inspection/English_TQI/out/unmatched.json'
        tid, question, answers, opts, solutions, _type = parse_data(query)
        if grade_subject in ['senior_english','junior_english']:
            if _type in ['阅读理解']:
                result_dict = self.matching_1(answers, solutions)
                if result_dict['flag'] == False:
                    result_dict = self.matching_2(answers, solutions, result_dict)
                    if result_dict['flag'] == False:
                        result_dict = self.matching_4(answers, solutions, result_dict)
                        # if result_dict['flag'] == False:
                            # result_dict = self.check_mix(answers, solutions, result_dict)
                # return result_dict

            elif _type in ['填空题']:
                # 已优化
                result_dict = self.matching_2(answers, solutions)
                # return result_dict

            elif _type in ['七选五','语法填空']:
                # 已优化
                result_dict = self.matching_1(answers, solutions)
                if result_dict['flag'] == False:
                    result_dict = self.matching_2(answers, solutions, result_dict)
                # if result_dict['flag'] = False and tid_type == '单选题':
                # return result_dict

            elif _type in ['单选题','完形填空']:
                # 已优化
                result_dict = self.matching_1(answers,solutions)
                # return result_dict

            elif _type in ['短文改错']:
                result_dict = self.matching_2(answers, solutions)
                if result_dict['flag'] == False:
                    result_dict = self.matching_3(answers, solutions, result_dict)
                # return result_dict

            elif _type in ['书面表达']:
                result_dict = self.matching_4(answers, solutions)
                if result_dict['flag'] == False:
                    result_dict = self.matching_2(answers, solutions, result_dict)
                # return result_dict

            else:
                result_dict = {}

            # error_detail = dict()
            tid_error = dict()
            unmatch_error_dict = dict()
            if result_dict:
                if result_dict['flag'] == False:
                    des = result_dict["description"]
                    source = None
                    target = None
                    pos = None
                    _type = result_dict["error_type"]
                    replace = 0
                    unmatch_error_detail = make_dict(des, source, target, pos, _type, replace)
                    tid_error["error_sent"] = result_dict['error_sent']
                    tid_error["error_detail"] = [unmatch_error_detail]
                    # error_detail['error_type'] = result_dict['error_type']
                    # error_detail['description'] = result_dict['description']
                    # tid_error['error_sent'] = None
                    # tid_error['error_detail'] = [error_detail]
                    unmatch_error_dict[tid] = [tid_error]
                    return unmatch_error_dict
            return unmatch_error_dict