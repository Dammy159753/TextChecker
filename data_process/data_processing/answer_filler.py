# !/usr/bin/python3
# -*- coding:utf-8 -*-
# @Author : licheng
# @Time   : 2020-05-22 10:37
import re
from collections import defaultdict


def list2string(array):
    array_str = ''
    for item in array:
        if isinstance(array, list):
            array_str = array_str.join('').join(item)
        else:
            array_str = array_str + ' ' + item
    return array_str


def sub_answers(answers, options):
    """
    提取answers所对应的选项，多选题时则将所有答案拼在一起输出
    :param answers: 答案选项 A, B, C, .. 可以是字符串，可以是列表
    :param options: 各选项
    :return:
    """
    concat_answer = ''
    if isinstance(answers, list):
        answers = list2string(answers)
    opt_answer = ''.join(answers)
    opt_answer = re.sub(r'[0-9()（） ]+', '', opt_answer)
    opt_answer = re.sub(r'Ａ', 'A', opt_answer)
    opt_answer = re.sub(r'Ｂ', 'B', opt_answer)
    opt_answer = re.sub(r'Ｃ', 'C', opt_answer)
    opt_answer = re.sub(r'Ｄ', 'D', opt_answer)
    if isinstance(answers, list) or len(opt_answer) <= 1:
        for opt in opt_answer:
            try:
                the_answers = '【' + options[opt.strip()] + '】'
            except:
                the_answers = '【】'
            concat_answer += the_answers
    else:
        opt_trues = re.findall(r'选([A-J])', opt_answer)
        try:
            for opt_true in opt_trues:
                the_answers = '【' + opt_answer.replace('选' + opt_true, '为' + options[opt_true.strip()]) + '】'
                concat_answer += the_answers
        except:
            concat_answer = ''
    return concat_answer


def tile_answer(answers):
    """
    将答案展开依次放入一个列表中
    :param answers: 输入的答案可能是列表或字符串
    :return:
    """
    if isinstance(answers, str):
        tile_ans = ['【' + answers + '】']
    else:
        tile_ans = ['【' + ans + '】' for ans in answers]
    return tile_ans


def generate_answer(question, options, answers):
    """
    自动将答案，如果是选择题则将对应的选项填入问题中
    :param question:
    :param options:
    :param answers:
    :return:
    """
    answer_lst = []
    if isinstance(answers, list):
        # *****************************************************************
        # if not options: 则options 为 "", 而answers为list.
        #                 该题有多个值["发电机", "内燃机", "汽车"] 对应options 为 ''
        # else: 则options必为列表, 分3种情况讨论,
        #   当 opts: ['op1', 'op2', 'op3', 'op4'] 时:
        #   要么 opt1 全为 "", 则为len(opts)个题，且没有选择题;
        #   要么 opt i 全部为 ""，这种情况为多选题
        #
        #   当 opts: [['op1', 'op1', 'op1', 'op1'], ['op1', 'op1', 'op1', 'op1'], ...] 时:
        #   则为多个单选题组成
        #
        #   当 opts 为 ["", ["opt1", "opt2", "opt3", "opt4"]] 混合型:
        #   这种情况为选择题跟非选择题的混合, 但个数应该跟answers个数相同:
        #   当 opt 为 "" 时，则为非选择题 否则为选择题
        # ************************************************************
        if options:  # 选择题
            flag = set()
            for opt in options:
                if isinstance(opt, dict) or not opt:
                    flag.add("dict")
                elif isinstance(opt, str):
                    flag.add("str")

            if "dict" in flag and (len(answers) == len(options)):  # 多个题
                for i, answer in enumerate(answers):
                    if options[i]:
                        concat_answer = sub_answers(answer, options[i])
                        answer_lst.append(concat_answer)
                    else:
                        tile_ans = tile_answer(answer)
                        answer_lst.extend(tile_ans)

            else:  # 单选题
                concat_answer = sub_answers(answers, options)
                answer_lst.append(concat_answer)

        else:
            answer_lst = tile_answer(answers)  # 直接展开答案

    else:
        if options:
            concat_answer = sub_answers(answers, options)
            answer_lst.append(concat_answer)
        else:
            answer_lst = tile_answer(answers)  # 直接展开答案

    sub_question = sub_info_questions(question, answer_lst)

    return answer_lst, sub_question


def sub_info_questions(question, answers):
    """
    将自动答案填充在括号或横线上，当答案少于则去除括号跟横线后将所有答案拼接在最后
    如果答案多余空格或连线时，将多余的答案拼接起来放到最后
    :param question: 带括号或横线待填充的问题
    :param answers:  答案，需要将答案填充在问题中
    :return: 填充后的问题
    """
    sub_question = ''
    flags = re.sub(r'[（(][ 　]*[）)]|_{3,}|\[[ 　]+\]_*', '轣', question)
    split_question = re.findall(r'[^轣]+', flags)
    flags = re.sub(r'[^轣]+', '轟', flags)
    i, j = 0, 0
    len_res = len(answers)
    len_space = len(re.findall(r'轣', flags))
    if len_res >= len_space:
        remain_answer = ''.join(answers[len_space:])
        sign_answers = answers[: len_space]
    else:
        remain_answer = ''.join(answers)
        sign_answers = ["" for i in range(len_space)]

    for flag in flags:
        if flag == '轣':
            if i <= len_res:
                sub_question += re.sub(r'（[0-9]+）|①②③④⑤⑥⑦⑧⑨⑩+', '', sign_answers[i])
                i += 1
        else:
            sub_question += split_question[j]
            j += 1
    sub_question += remain_answer
    return sub_question


def data_process(js_file, labs):
    """
    数据预处理，将数据清洗
    :param js_file:
    :param labs:
    :return:
    """
    question_infos = defaultdict(dict)
    for _, questions in js_file.items():
        opts = questions['opts']
        question = questions['question'].replace('【', '<').replace('】', '>')
        question = re.sub(r'(?:\t[(（] *[0-9]+ *[）)]){2,}', '', question)
        question = question.replace('\theta', 'θ')
        answers = questions['answers']
        labels = questions['labels']
        split_title = question.split('\t')
        save_ans = []
        try:
            if len(split_title) == 1:
                sub_questions = split_title[0]
                save_ans, save_questions = generate_answer(sub_questions, opts, answers)
                
                if labs:
                    question_infos[_] = {'question': save_questions, 'answers': save_ans,
                                        'opts': [list(opt.values()) if isinstance(opt, dict) else opt for opt in opts],
                                        'labels': labels}
                else:
                    question_infos[_] = {'question': save_questions, 'answers': save_ans,
                                        'opts': [list(opt.values()) if isinstance(opt, dict) else opt for opt in opts]}
            else:
                sub_questions = split_title[1:]
                if len(sub_questions) == len(answers) == len(opts):
                    save_question = split_title[0]
                elif (len(sub_questions) + 1) == len(answers) == len(opts):
                    save_question = ''
                    sub_questions = split_title
                else:
                    continue

                for i, sub_question in enumerate(sub_questions):
                    tags = re.findall(r'[（(][ 　]*[）)]|_{3,}|\[[ 　]+\]_*', sub_question)
                    if not tags:
                        if opts[i]:
                            answer = sub_answers(answers[i], opts[i])
                        else:
                            answer = "【{}】".format(answers[i])
                            save_question += sub_question + answer
                    else:
                        answer, the_question = generate_answer(sub_question, opts[i], answers[i])
                        save_question += ' ' + the_question
                    save_ans.append(answer)
                if labs:  
                    question_infos[_] = {'question': save_question, 'answers': save_ans, 'opts': [list(opt.values()) if isinstance(opt, dict) else opt for opt in opts], 'labels': labels}
                else:
                    question_infos[_] = {'question': save_question, 'answers': save_ans, 'opts': [list(opt.values()) if isinstance(opt, dict) else opt for opt in opts]}
        except Exception as e:
            question_infos[_] = questions
    return question_infos
