#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author : dyu
# @Time: 2020-11-23
# @Function: 

import re
from logserver import log_server
from LAC import LAC
from zh_utils import SYM_MAP, FIND_LIST, PUNCTUATION,ANSWER_LIST
from zh_utils import pump_list, getChineseStopWord, check_full_width


class AQCMatch:
    def __init__(self, lac, question, answer, solution, stems, subject):
        self.lac = lac
        self.answer = pump_list(answer)
        self.solution = solution
        self.stems = stems
        self.question = question
        self.subject = subject
        self.ErrorSet = []
        self.parse()

    def parse(self):
        option = []
        for stem in self.stems:
            if "stem" in stem.keys():
                self.question+='\n'+stem['stem']
            if "options" in stem.keys():
                option.append(stem['options'])
        self.option = option

    def removeSub(self, ans):
        """
        删除小题号 （1）（2）（3）等
        """
        p1 = re.compile(r'[（\(]\d+[）\)]')
        ans = re.sub(p1, '', ans)
        return ans

    def singleChoose(self, solution, i, ans):
        """
        答案A 与故选A 校验
        对solution进行 小题号删除， 一些符号删除， 空格删除，全角转半角等操作。
        对opt也进行以上步骤。
        首先， 我们要判断， 答案ABCD是否已以下 “故选”， “故填”，“正确答案”等形式存在在solution中。
        再判断， 是否以另外的形式存在。
        如果以上的pattern都不符合， 则用选项中的内容与解答进行校验。
        如果以上的所有都匹配不成功，则ErrorSet添加错误类型，并添加错误类型的描述。
        """
        # print(solution, self.option, i, ans)
        ans = self.removeSub(ans).strip()

        #对solution进行 小题号删除， 一些符号删除， 空格删除，全角转半角等操作。
        solu = solution[i]
        solu = self.removeSub(solu)
        solu = re.sub(r'[{}]'.format(PUNCTUATION), '', solu)
        solu = re.sub(r' ', '', solu)
        solu = check_full_width(solu)

        if len(self.option) == len(solution):
            # 对solution进行 小题号删除， 一些符号删除， 空格删除。
            opt = self.removeSub(self.option[i][ans])
            opt = re.sub(r'[{}]'.format(PUNCTUATION),'',opt)
            opt = re.sub(r' ','',opt)
        else:
            # 对solution进行 小题号删除， 一些符号删除， 空格删除。
            opt = self.removeSub(self.option[0][ans])
            opt = re.sub(r'[{}]'.format(PUNCTUATION), '', opt)
            opt = re.sub(r' ', '', opt)

        # Patterns
        index = solu.rfind('故选')
        index1 = solu.rfind('正确答案')
        index2 = solu.rfind('故填')
        index3 = solu.rfind('故为')
        index4 = solu.rfind('合理的是')
        pattern = '故' + ans + '正确'
        pattern1 = ans + '符合题意'
        pattern2 = ans + '符合'
        pattern3 = ans + '项'
        pattern4 = ans + '说法正确'
        pattern5 = re.compile(r'({}选项.*正确)'.format(ans))
        pattern6 = re.compile(r'(答案.*{})'.format(ans))
        pattern7 = re.compile(r'(选.*{})'.format(ans))
        pattern8 = re.compile(r'(故.*{})'.format(ans))
        pattern9 = re.compile(r'符合题意.*{}'.format(ans))

        #首先判断，在solution中是否有'故选'，'故填'等字眼
        if (index != -1) | (index1 != -1) | (index2 != -1) | (index3 != -1) | (index4 != -1) :
            if (ans in solu[index:]) | (ans in solu[index1:]) | (ans in solu[index2:]) | (ans in solu[index3:]) \
                    | (ans in solu[index4:]):
                pass
            elif (solu.startswith(ans)):
                pass
            else:
                self.ErrorSet.append(['答案{}与解答不匹配, 题型：选择题'.format(ans), 'zh_answer_unmatch_error', (index, len(solu))])

        #判断是否有此pattern存在在解答中，例如：‘A符合题意’，‘A项’等情况存在
        elif (pattern in solu) | (pattern1 in solu) | (pattern2 in solu) | (pattern3 in solu) | (pattern4 in solu):
            pass

        # 判断答案是否存在在解答的开头。
        elif (solu.startswith(ans)):
            pass

        #判断是否能在解答中找到以下正则的pattern. 例如：‘A选项正确’，‘答案为/是/()A’等情况存在
        elif (len(re.findall(pattern5, solu)) > 0) | (len(re.findall(pattern6, solu)) > 0) \
                | (len(re.findall(pattern7, solu)) > 0) | (len(re.findall(pattern8, solu)) > 0)\
                |(len(re.findall(pattern9,solu)) >0):
            pass

        #判断option是否在solution中存在。
        elif(opt in solu):
            pass

        # 否则，则往ErrorSet中添加错误信息。
        else:
            if self.subject == '物理' or self.subject == '化学' or self.subject == '数学':
                pass
            else:
                count = 0
                result_list = set()
                result_list = self.matchFindList(opt, result_list)

                for res in result_list:
                    if res in solu:
                        count += 1
                if count > 0:
                    pass
                else:
                    self.ErrorSet.append(['答案{}与解答不匹配,题型：选择题'.format(ans),
                                          'zh_answer_unmatch_error', None])


    def answerMatch(self):
        """
        选择题： 答案 A 与 解答中的故选A 相匹配校验
        首先确保选择题的选项不为空。否则返回错误类型：type_unmatch_error
        有两种情况：
        (1)答案的长度，与解答的长度相对应。
            例如答案【A, C】,解答则（1）...【A】， (2)...【C】
                或者 答案【A】， 解答..【A】
            此情况还有一种情况是为内嵌多选题。
            例如答案【【A,C】【B,C】】,
            解答则为 (1)...【A,C】. (2)...【B,C】
        (2)答案的长度 与解答的长度不对应。 （此类型多为多选题）
            例如答案【A,C】， 解答则为... 【故AC】。
        """
        self.ErrorSet = []
        count_1 = 0
        _index = []
        pattern = re.compile(r'[A-Za-z]')

        #情况一：当答案长度与解答长度相对应时
        if len(self.solution) == len(self.answer):
            #情况1.1： 判断答案是否为字符串
            if type(self.answer) == str:
                if len(self.answer)>1 and len(self.answer) == len(self.option):
                    for i, ans in enumerate(self.answer):
                        if len(re.findall(pattern, ans))>0 and len(ans)==1:
                            self.singleChoose(self.solution, i, ans)
                else:
                    if len(re.findall(pattern, self.answer))>0 and len(self.answer)==1:
                        self.singleChoose(self.solution, 0, self.answer)

            #情况1.2：如若答案为列表， 则每个遍历，与solution校验。
            else:
                for i, ans in enumerate(self.answer):
                    #情况1.3：如若列表中存在列表， 则把第二个列表的答案合并，再与解答相对应。
                    if type(ans) == list:
                    #     ans = ''.join(ans)
                        for an in ans:
                            if len(re.findall(pattern, an))>0 and len(an)==1:
                                self.singleChoose(self.solution, i, an)
                    else:
                        if len(re.findall(pattern, ans))>0 and len(ans)==1:
                            self.singleChoose(self.solution, i, ans)

        #情况二：如若答案长度与解答不相等时。
        else:
            # 则逐一遍历并与解答相匹配。
            for ans in self.answer:
                if len(re.findall(pattern, ans))>0 and len(ans)==1:
                    self.singleChoose(self.solution, 0, ans)

        if len(self.ErrorSet) > 0:
            return self.ErrorSet
        else:
            return None

    def matchFindList(self, sent, result_list):
        """
        对句子进行词性标注分词， 然后遍历分词后的词性，如若在我们FIND_LIST中 【n, nz, an 等】，
        且此单词不在停用词表中， 则添加进result_list.
        """
        sent_list = self.lac.run(sent)
        for _index, r in enumerate(sent_list[1]):
            if (self.subject == '物理') | (self.subject == '政治') | (self.subject == '生物'):
                if r in FIND_LIST+['v','ad','vn']:
                    if sent_list[0][_index] not in getChineseStopWord():
                        result_list.add(sent_list[0][_index])
            else:
                if r in FIND_LIST:
                    if sent_list[0][_index] not in getChineseStopWord():
                        result_list.add(sent_list[0][_index])
        return result_list

    def findpattern(self, result_list, sent):
        """找出所有match的result list"""

        #对句子进行小题号删除， 空格制表符的删除， 判断句子中是否存在公式。
        sent = self.removeSub(sent)
        sent = re.sub(r'[\t\s]', '', sent)
        p2 = re.compile(r'(\$\{.+?\}\$)')
        value = re.findall(p2, sent)

        #然后如果存在公式对公式进行提取，并用空格代替。并对一些简单的符号进行删除。
        sent = re.sub(r'(\$\{.+?\}\$)', ' ', sent)
        sent = re.sub(r'[．；]', '', sent)

        # 如果句子在进行上述操作后， 为ANSWER_LIST里的‘如解答所示’等的内容。则跳过。
        if sent.strip() not in ANSWER_LIST:

            #如若句子为空，则跳过。
            if (len(sent) != 0):

                #如果句子中存在LaTeX公式， 则需要对剩下的字符进行分词，词性匹配等操作。
                if (len(value) > 0):
                    sent = re.sub(r'[{}]'.format(PUNCTUATION), '', sent).strip()
                    result_list = self.matchFindList(sent, result_list)
                else:

                    # 如果句子中不存在公式，且长度短于4且词语不在停用词表中，则直接往result_list中添加。
                    if (len(sent) < 4) & (sent not in getChineseStopWord()):
                        sent = re.sub(r'[{}]'.format(PUNCTUATION), '', sent).strip()
                        result_list.add(sent)

                    #否则，则进行分词，词性匹配等操作。
                    else:
                        result_list = self.matchFindList(sent, result_list)

        return result_list, sent

    def optSolu(self, ans, ii, count):
        """
        答案选项内容与解答进行匹配。
        """
        if count is not None:
            option = self.option[ii][ans]

            #如若答案选项中的内容为空，返回异常，无法判断是否为图片还是真的为空。。
            if len(option) == 0:
                return None

            #题干加选项内容与解答进行匹配。
            questionOpt = self.question + option

            # 返回题干加选项内容的所有关键字。
            result_list = set()
            result_list_opt, _ = self.findpattern(result_list, option)
            if len(result_list_opt) > 0:
                result_list, _ = self.findpattern(result_list, questionOpt)
            else:
                # 选项内容只为公式，跳过文字匹配
                count += 1
                return count

            #对解答进行符号删除， 空格删除等基本操作。
            solu = re.sub(r'[{}]+'.format(PUNCTUATION), '', self.solution[ii])
            solu = re.sub(r' ', '', solu)

            #如果返回的关键字列表不为空，则继续以下判断。
            if result_list is not None:

                #如果返回的关键字列表的长度不为0，则继续以下判断。
                if len(result_list)>0:
                    for ans in result_list:

                        #如果关键字不为停用词，且在solution中出现，则匹配成功。
                        if ans not in getChineseStopWord():
                            if ans in solu:
                                count += 1
                            else:
                                pass
                else:
                    count+=1

            # 如若为空，则跳过。 （一般为选项中，或句子中只有公式，文字校验不对公式进行校验。所以跳过。）
            else:
                count +=1
        return count


    def ansContMatch(self):
        """
        题干加选项与解答进行匹配。
        情况1: 判断选项是否为空， 如若为空，则题型不匹配。 （选择题选项不能为空）
        情况2：判断选项的长度是否与解答的长度相匹配。
            2.1 判断答案是否为列表，还是为字符串。
                2.1.1 为列表，则遍历列表中的字符串并把对应答案的选项和解答传到optSolu的方法里面进行下一步校验。
                2.1.2 为字符串， 则直接答案， 对应的选项，传到optSolu的方法中进行下一步校验。
        情况3：当答案长度大于选项，解答时， 则遍历答案，并把答案一一与解答和选项相对应。
        情况4: 当答案长度与解答或选项不对应时，此为特殊例子。 待优化。
        """
        self.ErrorSet = []
        count = 0
        # 情况1
        if all(self.option):
            #情况2
            if len(self.option) == len(self.answer):
                for ii, ans in enumerate(self.answer):
                    #情况2.1.1
                    if type(ans) == list:
                        for a in ans:
                            a = self.removeSub(a)
                            count = self.optSolu(a, ii, count)
                    #情况2.1.2
                    else:
                        ans = self.removeSub(ans)
                        count = self.optSolu(ans, ii, count)

            #情况3
            elif (len(self.option) < len(self.answer)) & (len(self.option) == 1) & (
                    len(self.solution) < len(self.answer)) & (len(self.solution) == 1):
                for ans in self.answer:

                    #情况3.1:当选项为列表时，需要一一遍历对应校验
                    if type(ans) == list:
                        for a in ans:
                            a = self.removeSub(a)
                            count = self.optSolu(a, 0, count)

                    #情况3.2：当选项为字符串时，直接校验
                    else:
                        ans = self.removeSub(ans)
                        count = self.optSolu(ans, 0, count)

            #情况4
            else:
                log_server.logging('specialCase', len(self.option), len(self.answer), len(self.solution))

            if count is not None:
                if count > 0:
                    return None
                else:
                    # 返回 题干选项解答不匹配错误。
                    self.ErrorSet.append(['（题干加选项内容）与解答不匹配', 'zh_qos_unmatch_error'])
                    return self.ErrorSet
            else:
               # 选项内容为空
               return None
        else:
            # 选项为空
            return None

    def ansOptSolu(self, sentence):
        """
        此为解答题，填空题，简答题，材料分析题等的答案与解答相校验匹配。
        情况1：答案为字符串。
            情况1.1：判断如果答案是否只有符号存在。如果是则返回空。否则进行findpattern的方法进行校验，返回关键字。
        情况2：答案为列表
            情况2.1：对列表中的每个列表进行遍历， 如果列表中为列表， 则再对列表中的列表进行一一提取校验。
            情况2.2：如果列表中的为字符串，则直接进行校验。
        """
        result_list = set()
        #情况1
        if type(sentence) == str:

            #情况1.1
            if sentence.strip() not in PUNCTUATION:
                result_list, sent = self.findpattern(result_list, sentence)
            else:
                return None

        #情况2
        else:
            for sent in sentence:

                #情况2.1
                if type(sent) == list:
                    for s in sent:
                        if s.strip() not in PUNCTUATION:
                            result_list, sent = self.findpattern(result_list, s)
                        else:
                            return None

                #情况2.2
                else:
                    if sent.strip() not in PUNCTUATION:
                        result_list, sent = self.findpattern(result_list, sent)
                    else:
                        return None
        return result_list

    def quesSolu(self, sentence):
        """
        此为解答题，填空题，简答题，材料分析题等的题干与解答相校验匹配。
        题干中的情况没有那么多， 如果题干为列表， 则把整个列表连接起来成字符串。然后删除制表符和空格
        然后进行分词，词性标注的分析提取，返回关键字。
        """
        result_list = set()

        if type(sentence) == list:
            sentence = ''.join(sentence)
        sentence = re.sub(r'[\t\s]', '', sentence)
        result_list,_ = self.findpattern(result_list,sentence)
        return result_list



    def ansMatch(self, ans, ques):
        """
        对解答题等的题干，答案，与解答校验。
        """
        self.ErrorSet = []
        count = 0

        #把解答中的所有内容整合起来， 不按照小题号相对应。并把删除所有的空格
        solution = pump_list(self.solution)
        if type(solution) == list:
            solution = ''.join(solution)
        solution = re.sub(r' ', '', solution)
        if len(solution)>50:
            #如果_type为真，则进行答案与解答校验；否则进行题干与解答校验。
            # if _type:
            resultAns = self.ansOptSolu(ans)
            # else:
            resultQues = self.quesSolu(ques)
            if resultAns is not None:
                if len(resultAns) > 0:
                    if (resultQues is not None):
                        result = list(resultAns) + list(resultQues)
                    else:
                        result = list(resultAns)
                else:
                    # 如果resultAns长度为0 的话， 那么答案可能只有公式，因此不必要做文字匹配
                    return None
            else:
                # 如果resultAns为空的话， 则答案仅有标点符号， 此题型可能为连线题。因此不必要做文字匹配
                return None


            #判断result_list是否为空， 为空则代表答案或者题干为空，或者只有标点符号的存在， 无实际内容。
            if result is not None:

                #如果result的长度不为0， 则进行下列操作。
                if len(result) > 0:
                    for res in result:
                        res1 = res.strip()
                        solution = re.sub(r'[{}]'.format(PUNCTUATION), '', solution)
                        if res1 in solution:
                            count += 1
                        else:
                            pass
                #如果result 的长度为0， 则代表，答案或题干中，只有公式， 无其他文字内容。
                else:
                    return None
            else:
                # 返回答案为空的错误
                return None

            if count > 0:
                return None
            else:
                self.ErrorSet.append(['题干答案与解答不匹配', 'zh_qas_unmatch_error'])
                return self.ErrorSet
        else:
            return None


