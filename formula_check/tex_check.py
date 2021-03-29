#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TeX Checker    NDD   21/03/08  (translated from bash/awk to python, 30/08/19)
# Script for performing various checks on TeX files.
# @Time   : 2020/12/9
# @Author : dyu
# @File : tex_check.py
# @Function : Tex检测

import re
import sys
import math
import textwrap as tw

class TexChecker(object):
    def __init__(self):
        self.error_detail = []
        self.romannumeralre = re.compile(r"^[IVXLCDM]*$") # Regular expression for matching Roman numerals.

    def stripcomments(self, fstr):
        """Get rid of comments and verbatim sections."""
        fstr_new=re.sub(r"^[ \t]*%.*$","",fstr,flags=re.MULTILINE)
        fstr_new=re.sub(r"^(.*[^\\\n])%.*$",r"\1",fstr_new,flags=re.MULTILINE)
        fstr_new=re.sub(r"\\begin\{verbatim\}.*?\\end\{verbatim\}",
                        r"\\begin{verbatim} \\end{verbatim}",fstr_new,
                        flags=re.DOTALL)
        fstr_new=re.sub(r"\\begin\{lstlisting\}.*?\\end\{lstlisting\}",
                        r"\\begin{lstlisting} \\end{lstlisting}",fstr_new,
                        flags=re.DOTALL)
        return fstr_new

    def stripeqns(self, fstr):
        """Get rid of standalone equations."""
        fstr_new=re.sub(r'(\\begin\{(math|equation\*?|displaymath'
                        r'|eqnarray\*?|align)\}|\\[\(\[]).*?(\\end\{(math'
                        r'|equation\*?|displaymath|eqnarray\*?|align)\}|\\[\]\)])',
                        r"\1 xxx \3",fstr,flags=re.DOTALL)
        return fstr_new

    def stripinline(self, fstr):
        """Get rid of inline equations."""
        fstr_new=re.sub(r"([^\\])\$\$.*?[^\\]\$\$",r"\1$xxx$",fstr,flags=re.DOTALL)
        fstr_new=re.sub(r"([^\\])\$.*?[^\\]\$",r"\1$xxx$",fstr_new,flags=re.DOTALL)
        return fstr_new

    def reportissues(self, x,message):
        """Report issues, giving lines where each issue occurs."""
        err = {}
        if x:
            err['error_type'] = 'fm_content_error'
            err['description'] = "{}: {}".format(message, x)
            self.error_detail.append(err)

    def checkat(self, fstr):
        """Check for missing \@."""
        x=re.findall(r"^.*\w[A-Z][\)\]']*\.[\)\]']*(?:[ \t~].*)?$",fstr,
                     re.MULTILINE)
        self.reportissues(x,r'need for "\@"')

    def checkdoubledots(self, fstr):
        """Look for double dots."""
        x=re.findall("^.*(?<!right)\.\..*$",fstr,re.MULTILINE)
        self.reportissues(x,"double dots")

    def checkdoublecapitalisation(self, fstr):
        """Look for double capitalisation."""
        excludes=("MHz","GHz","THz","MPa","GPa","TPa","MPhys","OKed","OKing",
                  "HCl","BSc","MSci")
        y=set(re.findall(r"[\s~]([A-Z][A-Z][a-z][a-z]+?|[A-Z][A-Z][a-rt-z])[\s~]",
                         fstr))
        z=[t for t in y if t not in excludes]
        if z:
            x=re.findall(r"^.*(?:"+r"|".join(z)+r").*$",fstr,re.MULTILINE)
            self.reportissues(x,"double capitalisation")

    def checkmissingcapitalisation(self, fstr):
        """Check for missing capitalisation."""
        x=re.findall(r"^.*\.[\)\]\}']*[\s~]+[a-z].*$",fstr,re.MULTILINE)
        self.reportissues(x,"missing capitalisation")

    def checkmissingbackslash(self, fstr):
        """Check for "e.g. XXX"."""
        x=re.findall(r"^.*(?:i\.e\.|e\.g.\|n\.b\.)(?:[ \t~].*)?$",fstr,
                     re.MULTILINE|re.IGNORECASE)
        self.reportissues(x,r'missing "\ "')
        x=re.findall(r"^.*a\.u\.\s+[a-z].*$",fstr,re.MULTILINE)
        self.reportissues(x,r'missing "\ "')

    def checkinvcommas(self, fstr):
        """Look for back-to-front inverted commas, etc."""
        x=re.findall(r"^.*[^\\\n]\".*$|^(?:.*[ \t~])?'.*$|^.*\`(?:[ \t~].*)?$",fstr,
                     re.MULTILINE)
        self.reportissues(x,"erroneous speech marks")

    def checkanconsonant(self, fstr):
        """Look for "an consonant"."""
        x=re.findall(r"^(?:.*[ \t~])?[Aa]n[\s~]+(?:[bcdfgjklmnpqrstvwxyz]"
                     r"|[BCDFGJKLMNPQRSTVWXYZ][a-z]).*$",fstr,re.MULTILINE)
        self.reportissues(x,r'"an consonant"')

    def checkavowel(self, fstr):
        """Look for "a vowel".  NB, one can have "a unicorn", etc."""
        x=re.findall(r"^(?:.*[ \t~])?a[\s~]+[aei].*$",fstr,
                     re.MULTILINE|re.IGNORECASE)
        self.reportissues(x,r'"a vowel"')

    def checkerthat(self, fstr):
        """Look for "er that"."""
        excludere=re.compile(r"(?:remember|order|layer|however|compiler|power"
                             r"|parameter|barrier)[\s~]+that",re.IGNORECASE)
        y=re.findall(r"^.*er[\s~]+that[\s~].*$|^(?:.*[ \t~])?less[\s~]"
                     r"+that(?:[ \t~].*)?$",fstr,re.MULTILINE|re.IGNORECASE)
        x=[t for t in y if not excludere.search(t)]
        self.reportissues(x,r'"...er that"')

    def checkspacestop(self, fstr):
        """Look for " ."."""
        x=re.findall(r"^(?:.*[ \t~])?(?<!\\tt )[\.\,:;\?\!].*$",fstr,re.MULTILINE)
        self.reportissues(x,"space before punctuation mark")

    def checkstopcolon(self, fstr):
        """Look for ".: "."""
        x=re.findall(r"^.*\.:(?:[ \t~].*)?$",fstr,re.MULTILINE)
        self.reportissues(x,"need for backslash after colon")

    def checklyhyphen(self, fstr):
        """Look for "ly-"."""
        x=re.findall(r"^.*ly-[a-z].*$",fstr,re.MULTILINE|re.IGNORECASE)
        self.reportissues(x,"unnecessary hyphen")

    def checkneedendash(self, fstr):
        """Look for e.g. "3-6"."""
        x=re.findall(r"^(?:.*[^\{\d\n][ \t~]*)?\d+[\s~\$]*-[\s~\$]*\d.*$",
                     fstr,re.MULTILINE)
        self.reportissues(x,"need for an en-dash")

    def checkrep(self, fstr):
        """
        Check for repetition of of words.
        检查单词的重复。
        """
        excludes=(r"\hline",r"&",r"\\",r"\end{itemize}",r"\end{enumerate}",
                  r"\end{description}")
        excludesre=re.compile(r"^\d+,?$|^[A-Z]\.?\\?$")
        lw=""
        x=[]
        for l in fstr.splitlines():
            for iw,w in enumerate(l.split()):
                if w==lw and not w in excludes and not excludesre.search(w):
                    if iw==0:
                        x.append("... "+w+"\n"+l)
                    else:
                        x.append(l)
                lw=w
        self.reportissues(x,"repetition of words")

    def checkeqref(self, fstr):
        """
        Look for e.g. "Eq.\ \ref".
        """
        x=re.findall(r"^(?:.*[ \t~])?(?:[eE]qn?s?\.?\\?|[eE]quations?)[\s~]"
                     r"+(?:\\ref|\d).*$",fstr,re.MULTILINE)
        self.reportissues(x,r'"Eq.\ \ref" (brackets needed)')

    def checkeqspace(self, fstr):
        """
        Look for e.g. "Eq. ".
        """
        x=re.findall(r"^(?:.*[ \t~])?(?:[eE]qn?|[rR]ef|[fF]ig|[sS]ec)s?\.?"
                     r"(?:[ \t~].*)?$",fstr,re.MULTILINE)
        self.reportissues(x,r'missing "\ "')

    def checkwrongabbrev(self, fstr):
        """
        Look for e.g. "Sentence.  Eq. ".
        """
        x=re.findall(r"^.*\.\s+(?:Eqn?|Ref|Fig|Sec)s?\..*$",fstr,
                     re.MULTILINE|re.IGNORECASE)
        self.reportissues(x,"need to use nonabbreviated form at start of a sentence")

    def checkmissabbrev(self, fstr):
        """
        Look for e.g. "in Equation".
        """
        x=re.findall(r"^.*[A-Z,;:a-z]\s+(?:Equation|Reference|Figure|Section)"
                     r"[\s~]*(?:\(?\\ref|\d).*$",fstr,re.MULTILINE)
        self.reportissues(x,"need to use abbreviated form in middle of a sentence")

    def checkendash(self, fstr):
        """Look for " --"."""
        x=re.findall(r"^(?:.*[ \t~])?--.*$",fstr,re.MULTILINE)
        self.reportissues(x,"need to delete space before dash")
        x=re.findall(r"^.*[^\d\n]--(?:[ \t~].*)?$",fstr,re.MULTILINE)
        self.reportissues(x,"need to delete space after dash")

    def checkrefcase(self, fstr):
        """Look for e.g. "eq."."""
        x=re.findall(r"^(?:.*[ \t~])?(?:eqn?|fig|sec|table|ref)s?\.($:[ \t~].*)?$",
                     fstr,re.MULTILINE)
        self.reportissues(x,"need to use a capital letter")

    def checkminus(self, fstr):
        """
        Look for dodgy minus signs.
        寻找不好的减号。
        """
        x=re.findall(r"^(?:.*(?:[ \t~]|[^\{\n]\d))?-\d.*$",fstr,re.MULTILINE)
        self.reportissues(x,"need to use math mode for minus sign")

    def checknonascii(self, fstr):
        """
        Look for non-ASCII characters.
        查找非ASCII字符。
        """
        x=re.findall(r"^.*[^\x20-\x7E\x0A\x0D\n].*$",fstr,re.MULTILINE)
        self.reportissues(x,"non-printable-ASCII character(s)")

    def checkbib(self, fstr):
        """
        Check size of the bibliography.
        检查参考书目大小
        """
        nb=len(re.findall(r"\\bibitem",fstr))
        if nb>0:
            nd=int(math.log(float(nb))/math.log(10.0))+1
            if not re.search(r"\{thebibliography}{\d{"+str(nd)+r"}\}",fstr):
                bibmatch=re.search(r"\{thebibliography\}\{\d*\}",fstr)

    def checkfoils(self, fstr):
        """
        Look for things that shouldn't occur in foils.
        寻找书简中不应该存在的东西。
        """
        x=re.findall(r"^.*\\textit.*$",fstr,re.MULTILINE)
        self.reportissues(x,r'"\textit"')
        x=re.findall(r"^.*\\textsc.*$",fstr,re.MULTILINE)
        self.reportissues(x,r'"\textsc"')
        x=re.findall(r"^.*\\begin{equation}.*$",fstr,re.MULTILINE)
        self.reportissues(x,r'"equation"')
        x=re.findall(r"^.*\\footnote{[^~].*$",fstr,re.MULTILINE)
        self.reportissues(x,r'missing "~"')

    def checknotfoils(self, fstr):
        """
        Look for things that shouldn't occur in files that aren't foils.
        寻找不存在障碍的文件中不应该发生的事情。
        """
        x=re.findall(r"^.*\\textsl.*$",fstr,re.MULTILINE)
        self.reportissues(x,r'"\textsl"')
        x=re.findall(r"^.*\\begin{displaymath}.*$",fstr,re.MULTILINE)
        self.reportissues(x,r'"displaymath"')
        x=re.findall(r"^.*\\begin{eqnarray\*}.*$",fstr,re.MULTILINE)
        self.reportissues(x,r'"eqnarray*"')
        x=re.findall(r"^.*\\footnote{~.*$",fstr,re.MULTILINE)
        self.reportissues(x,r'"\footnote{~"')

    def checkwordcite(self, fstr):
        """Look for " \cite"."""
        x=re.findall(r"^(?:.*[ \t~])?\\cite.*$",fstr,re.MULTILINE)
        self.reportissues(x,r'" \cite"')

    def checksuperscriptcite(self, fstr):
        """Look for ".\cite"."""
        x=re.findall(r"^.*[^\s~\n]\\cite.*$",fstr,re.MULTILINE)
        self.reportissues(x,r'".\cite"')

    def checkacronyms(self, fstr):
        """
        Check whether acronyms are defined.  Exclude country names, etc.,
        and exclude Roman numerals.
        检查是否定义了首字母缩写词。 排除国家名称等，并排除罗马数字。
        """
        definedacronyms=("NDD","LA1","4YB","CB3","0HE","UK","USA","EU","UAE","OK",
                         "GNU","AMD","AOL","BAE","BMW","BP","CV","HSBC","IBM",
                         "KFC","CCSD")
        acronyms=set(re.findall(r"\s([A-Z][A-Z\d]+)(?:\\@)?[\s\.,;\.\!\?~']",fstr))
        undefined=[]
        for a in acronyms:
            if a in definedacronyms or self.romannumeralre.search(a): continue
            if not re.search(r"\("+a+r"(?:\\@|s)?\).*\s"+a
                             +r"(?:\\@)?[\s\.,;\.\!\?~']",fstr,re.DOTALL):
                undefined.append(a)
        if undefined:
            print(purple+"Possible need to define the following acronyms:"+default)
            print(tw.fill(", ".join(undefined))+"\n")

    def checkmultipleacronyms(self, fstr):
        """
        Check whether acronyms are multiply defined.
        检查是否多次定义了首字母缩写词。
        """
        multiple=[]
        for sec in fstr.split(r"\end{abstract}"):
            acronyms=re.findall(r"\(([A-Z][A-Z\d]+)(?:\\@)?\)",sec)
            for a in set(acronyms):
                if not self.romannumeralre.search(a) and acronyms.count(a)>1:
                    multiple.append(a)
        if multiple:
            print(purple+"Possible multiple definitions of acronyms:"+default)
            print(tw.fill(", ".join(multiple))+"\n")

    def checker(self, fstr):
        """
        Tex checker
        :param fstr:
        :return:
        """
        # Main program starts here.
        foilsre=re.compile(r"\\documentclass.*foils",re.MULTILINE)
        aipre=re.compile(r"\\documentclass.*(?:aip\s*[,\]]|achemso)",re.MULTILINE)
        natre=re.compile(r"\\documentclass.*nature",re.MULTILINE)

        # Get rid of comments and verbatim stuff.
        fstr=self.stripcomments(fstr)
        # Text only versions.
        fstr_noeqns=self.stripeqns(fstr)
        fstr_nomath=self.stripinline(fstr_noeqns)

        # What sort of TeX file do we have (AIP / Nature / Foils)?
        aip=bool(aipre.search(fstr))
        nat=bool(natre.search(fstr))
        foils=bool(foilsre.search(fstr))

        self.checknonascii(fstr)
        self.checkdoubledots(fstr)
        self.checkat(fstr_noeqns)
        self.checkdoublecapitalisation(fstr_nomath)
        self.checkmissingcapitalisation(fstr_noeqns)
        self.checkmissingbackslash(fstr_noeqns)
        self.checkinvcommas(fstr)
        self.checkanconsonant(fstr_nomath)
        self.checkavowel(fstr_nomath)
        self.checkerthat(fstr_noeqns)
        self.checkspacestop(fstr_noeqns)
        self.checkstopcolon(fstr_noeqns)
        self.checklyhyphen(fstr_noeqns)
        self.checkneedendash(fstr_noeqns)
        self.checkrep(fstr_noeqns)
        self.checkeqref(fstr_noeqns)
        self.checkeqspace(fstr_noeqns)
        self.checkwrongabbrev(fstr_noeqns)
        if not nat: self.checkmissabbrev(fstr_noeqns)
        self.checkendash(fstr_nomath)
        self.checkrefcase(fstr_noeqns)
        self.checkminus(fstr_nomath)

        if len(self.error_detail) != 0:
            return self.error_detail
        else:
            return None
            
if __name__ == '__main__':
    A = '\\angle ACB= 90^{{\\circ}你好 }'
    tex = TexChecker()
    error_detail = tex.checker(A)

    print(error_detail)