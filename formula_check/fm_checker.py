#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time   : 2020/11/17 - 17:03
# @Modify : 2020/12/18 - 16:43
# @Author : dyu
# @File : fm_checker.py
# @Function :

import re
import latex2mathml.converter

from tex_check import TexChecker
from latex_utils import fm_read_json, extract_formula, latex_translation, check_latex_symbol_repeat, check_latex_illegal_symbol, check_latex_func_name, check_latex_brackets, Textidote, FormatCheck


class FmChecker(object):
    def __init__(self, mode):
        self.mapping_names = fm_read_json(r'formula_check/LaTexMap/latex_map.json')
        self.tex = TexChecker()
        self.mode = mode
        self.format_checker = FormatCheck()
        # self.latexer = latex_parser.BaseProcessLatex()

    def latex_content_check(self, text, subject=None):
        """
        Latex 内容检测主方法
        :return:
        """
        error_details = list()    # 所有的错误集合
        extract_latexs = extract_formula(text)
        
        # 括号格式缺失校验
        scheme_err = self.format_checker.check_scheme(text)

        if scheme_err is not None:
            error_details.append(scheme_err)

        for e_latex in extract_latexs:
            ## 1. 不允许同一符号多次出现
            if 'symbol_repeat' in self.mode:
                err_1 = check_latex_symbol_repeat(e_latex)
                if err_1 is not None:
                    error_details.append(err_1)

            # 2. 公式中不允许出现的符号
            if 'illegal_symbol' in self.mode:
                err_2 = check_latex_illegal_symbol(e_latex)
                if err_2 is not None:
                    error_details.append(err_2)

            # 3. 不允许函数名写错 和 \\函数后面只能加{}，否者要空格, 校对函数名称暂时只针对'数学'
            if 'func_name' in self.mode:
                err_3 = check_latex_func_name(e_latex, self.mapping_names)
                if err_3 is not None:
                    error_details.extend(err_3)

            ## 4. 不允许公式中出现括号不对称，在预处理格式不匹配已经完成
            if 'brackets' in self.mode:
                err_4 = check_latex_brackets(e_latex)
                if err_4 is not None:
                    error_details.append(err_4)

            ## 5. 采用latex2mathml检测, 然后在检测mathml是否能渲染或语法检错
            if 'latex2mathml' in self.mode:
                try:
                    latex2mathml.converter.convert(e_latex)
                except:
                    err_mathml = {}
                    err_mathml['error_type'] = 'fm_content_error'
                    err_mathml['description'] = "无法转换latex公式，请检查合理性."
                    error_details.append(err_mathml)

            ## 6. 采用texcheck 和 Tex2txt 两种Tex2txt检测
            if 'texcheck' in self.mode:
                err_61 = self.tex.checker(e_latex)
                if err_61 is not None:
                    error_details.append(err_61)

            ## 7. 采用textidote 检测
            if 'textidote' in self.mode:
                textidote = Textidote(e_latex)
                err_62 = textidote.dote_check()
                if err_62 is not None:
                    error_details.append(err_62)


        error_details = [err for err in error_details if len(err) != 0]
        if len(extract_latexs) != 0:
            return error_details, len(extract_latexs), extract_latexs
        else:
            return [], 0, extract_latexs



if __name__ == '__main__':

    A = '{\\mathrm{CaCO}}_3\\ xrightarrow{\\mathrm{高温}}\\   mathrm{CaO}+{\\mathrm{CO}}_2\\uparrow}'
    B = "阿斯蒂芬阿斯蒂芬阿斯蒂芬${\\angle {\g}ACB= 90^{\\clrc{k}}}$奥"
    C = "${\\angle ACB= 90^\\circ}$"
    mode = ['func_name', 'symbol_repeat', 'latex2mathml', 'textidote', 'illegal_symbol']
    fm_checker = FmChecker(mode)
    # fm_checker.latex_content_check(C)
    # fm_checker.latex_func_name_check(B)
    res = extract_formula(B)




