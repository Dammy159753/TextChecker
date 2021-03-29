import re
from en_utils import _read_json
from data_processing.answer_filler  import data_process
import jieba
# import jieba_fast as jieba

jieba.load_userdict('dataset/all_word_vocab.txt')
stopwords_path = 'dataset/stopword.txt'
stopwords = [line.strip() for line in open(stopwords_path, 'r', encoding='UTF-8').readlines()]


class DealLaTex:

    def __init__(self, sym_path):
        self.sym_dct = _read_json(sym_path)
        pass

    def process_latex(self, text):
        # 移除latex的开始与结束标记
        text = re.sub(r'\$', '', text)

        # 移除没有用的字符 <已加入词表>
        text = self.rm_mathrm(text)

        # 特殊字符替换
        text = self.sub_symbol(text)

        # 处理分式
        text = self.deal_formula(text)

        # 处理 ^ 跟 _
        text = self.underline_power(text)

        # 处理单独处理的特殊公式(先处理^ _)
        text = self.trans_special_symbol(text)

        # 格式整理
        text = self.unified_format(text)

        return text

    def rm_mathrm(self, text):
        text = re.sub(r'\\math[a-zA-Z]+', r'', text)
        return text

    def sub_symbol(self, text):
        # 特殊字符替换
        for latex, sym in self.sym_dct.items():
            text = text.replace(latex, sym)
        # text = re.sub(r'\{ *\{([^{}]*?)\} *\}', r'{\1}', text)
        return text

    def deal_formula(self, text):

        while True:
            start_text = text
            text = re.sub(r'(\\d?frac *\{[^{}]*?)\{([^{}]+)\}(.*?\})', r'\1(\2)\3', text)
            if start_text == text:
                break
        text = re.sub(r'\\d?frac *\{(.*?)\} *\{(.*?)\}', r'{\1}/{\2}', text)
        text = re.sub(r'd?frac *(.) *(.)', r'\1/\2', text)
        return text

    def underline_power(self, text):
        # 处理 ^ 跟 _
        text = re.sub(r'([_\^]) *(?:\{(.*?)\}|([^{}]))', r'\1\2\3 ', text)
        text = re.sub(r' +([_\^].*?)', r'\1', text)
        return text

    def trans_special_symbol(self, text):
        # 处理度与摄氏度 circ
        text = re.sub(r'\^ *° *C', r'℃', text)
        text = re.sub(r'\^ *°', r'°', text)

        # 处理带反应条件的字符 overset
        text = re.sub(r'\\overset *\{([^{}]*?)\}\{(?:[\\=!]+|\\rightarrow)\}', r' 反应条件\1 ', text)
        text = re.sub(r'\\overset *\{\\frown *\}\{(.*?)\}', r'弧\1 ', text)
        text = re.sub(r'\\overset *', r'', text)
        return text

    def unified_format(self, text):
        """归一化格式"""

        # 花括号移除
        text = re.sub(r'\\\{', r'&&&$', text)
        text = re.sub(r'\\\}', r'$&&&', text)
        while True:
            start_text = text
            # 部分括号/花括号移除
            text = re.sub(r'\(([a-z0-9 ]*)\)', r'\1', text)
            text = re.sub(r'\(( *. *)\)', r'\1', text)
            # text = re.sub(r'\{([a-z0-9]*.)\}', r'\1', text)

            text = re.sub(r'\{([^{}]*?)\}', r' \1 ', text)
            if start_text == text:
                break

        text = re.sub(r'&&&\$', r'{', text)
        text = re.sub(r'\$&&&', r'}', text)

        # 移除多余空格
        text = re.sub(r'([^_−]) *', r'\1', text)
        text = re.sub(r' +', ' ', text)
        text = re.sub(r' *\^?°', r'°', text)
        text = re.sub(r' *([>·()/=×<~≤≥∠≠△⊥≡±∈～]+) *', r'\1', text)
        text = re.sub(r'\( *\)', '', text)

        text = text.replace('&gt;', '≥')
        text = text.replace('&lt;', '<')
        text = text.replace('&amp;', '')
        text = text.replace('&', '')

        text = re.sub(r'\\xrightarrow\[\\,\]', '', text)
        text = re.sub('cases(.*?)cases', r'分段函数\1', text)
        text = text.replace(r'\\\\', '或')
        text = text.replace('^′', '′')
        text = re.sub(r'\\', '', text)
        text = text.replace('，', ',')
        text = re.sub(r'([,。 ])+', r'\1', text)

        return text


def clean_text(questions_dct, sym_dct_f='/media/chen2/dyu/SQR_training/src/dataset/new_latex_map.json'):
    res_question = dict()
    deal_latex = DealLaTex(sym_dct_f)
    # 答案填充
    fill_answer = data_process(questions_dct, labs=True)
    for tid, item in fill_answer.items():
        question = item['question']
        trans_question = deal_latex.process_latex(question)
        item['question'] = trans_question
        res_question[tid] = item
    return res_question

def sentence_split(sentence, use_stopwords=True):
    """
    切分 sentence
    取‘魑魅魍魉’生僻字是保证文本中不出现该类字，导致分词出错，其实是一种分割符
    """
    sentence = re.sub('[↓]', '', sentence)

    patten_other = re.compile(r'[^魑魅魍]+')

    patten_ion = re.compile(r'[a-zA-Z]*[\^][0-9]?[\+]')  # 2Fe^3+ [离子类化学式]
    ion = patten_ion.findall(sentence)
    flags_ion = patten_ion.sub('魑', sentence)

    char_set = ['+', '=', ',', '（', '）', '＝', '、', '.', '．', '⇌']
    molecular0 = []
    flags_molecular0 = flags_ion
    unChineseStr = ''
    for word in flags_ion:
        word = word.strip()
        if not '\u4e00' <= word <= '\u9fff' and word not in char_set:
            unChineseStr = unChineseStr + word
        else:
            if len(unChineseStr) >= 1:
                flags_molecular0 = flags_molecular0.replace(unChineseStr, '魅')
                molecular0.append(unChineseStr)
            unChineseStr = ''

    patten_molecular1 = re.compile(r'[a-zA-Z]+[_][0-9a-zA-Z]+')  #H_2S  (NH_4)_2Fe(SO_4)_2
    molecular1 = patten_molecular1.findall(flags_molecular0)
    molecular0.extend(molecular1)
    molecular1 = molecular0
    flags_molecular1 = patten_molecular1.sub('魅', flags_molecular0)



    patten_molecular2 = re.compile(r'[A-Z]*[a-z]')  # S Fe
    molecular2 = patten_molecular2.findall(flags_molecular1)
    flags_molecular2 = patten_molecular2.sub('魍', flags_molecular1)

    others = patten_other.findall(flags_molecular2)
    flags = patten_other.sub('魉', flags_molecular2)

    split_sentence = []
    ion_i, molecular1_i, molecular2_i, other_i = 0, 0, 0, 0
    for flag in flags:
        if flag == '魑':
            try:
                power_str = ion[ion_i]
                split_sentence.append(power_str)
                ion_i += 1
            except:
                pass
        elif flag == '魅':
            try:
                degree_str = molecular1[molecular1_i]
                split_sentence.append(degree_str)
                molecular1_i += 1
            except:
                pass
        elif flag == '魍':
            try:
                degree_str = molecular2[molecular2_i]
                split_sentence.append(degree_str)
                molecular2_i += 1
            except:
                pass
        elif flag == '魉':
            other_str = others[other_i]
            other_str = re.sub(r'[0-9]+', '', other_str)
            other_split = jieba.lcut(other_str)
            split_sentence.extend(other_split)
            other_i += 1
    if use_stopwords:
        sentence_lst = list()
        for i, word in enumerate(split_sentence):
            if word not in stopwords:
                word = re.sub('[ ①②③④⑤⑥⑦⑧⑨∵∴；\-：，。！？\?“”‘’（）:…【】△↑]', '', word)
                if len(re.findall('[()]', word)) % 2 != 0:
                    word = re.sub('[()]', '', word)
                try:
                    words = list(word)
                    if words[0].isdigit() and words[1].isupper():
                        words[0] = ''
                        word = ''.join(words).strip()
                except:
                    pass
                if not word.isdigit() and word not in 'ABCD':
                    sentence_lst.append(word)
    else:
        sentence_lst = split_sentence
    return sentence_lst

def cut_sent(para):
    para = re.sub('([。！？?])([^”’])', r"\1\n\2", para)  # 单字符断句符
    para = re.sub('(\.{6})([^”’])', r"\1\n\2", para)  # 英文省略号
    para = re.sub('(…{2})([^”’])', r"\1\n\2", para)  # 中文省略号
    para = re.sub('([。！？?][”’])([^，。！？?])', r'\1\n\2', para)
    # 如果双引号前有终止符，那么双引号才是句子的终点，把分句符\n放到双引号后，注意前面的几句都小心保留了双引号
    para = para.rstrip()  # 段尾如果有多余的\n就去掉它
    # 很多规则中会考虑分号;，但是这里我把它忽略不计，破折号、英文双引号等同样忽略，需要的再做些简单调整即可。
    return para.split("\n")

def read_sentences(para):
    sent_list = cut_sent(para)
    out_sentences = []
    for sent in sent_list:
        sentence = sentence_split(sent)
        out_sentences.extend(sentence)
    return out_sentences

if __name__ == '__main__':
    pass
