# encoding: utf-8

# Copyright (c) 2019-present, AI
# All rights reserved.
# @Time 2019/10/10
from sys import path
path.append("/media/Data/lndoremi/gec_online/gec_scripts/")
import argparse
import spacy
from addict import Dict
import os
from itertools import combinations
from nltk.stem.lancaster import LancasterStemmer
from GEC_check.gec_scripts.errant_scripts import align_text, cat_rules, toolbox
from GEC_check.lm_scorer import LMScorer

# import language_check


"""
作用： 对平行文件进行后处理
来自errant https://github.com/chrisjbryant/errant gec_postprocess.py 文件,
和 https://github.com/kakaobrain/helo_word
Thanks for their brilliant works
"""


class M2Filter(object):
    def __init__(self, filter_token=None, filter_type_lst=[],
                 lev=True, merge='rules', apply_LT=False,
                 apply_rerank=False, lm_path=None, lm_databin=None,
                 preserve_spell=False, max_edits=5, ):
        """

        :param filter_token:
        :param filter_type_lst: 过滤掉的类别，典型的可传入一些精度不高的类别['U:CONJ', 'U:VERB:FORM', 'U:ADV', 'M:ADJ',
                                                        'R:OTHER', 'R:NOUN', 'U:VERB', 'U:OTHER', 'U:NOUN']
        :param lev: Use standard Levenshtein to align sentences
        :param merge:
        choices=["rules", "all-split", "all-merge", "all-equal"], default="rules",
        help="Choose a merging strategy for automatic alignment.\n"
        "rules: Use a rule-based merging strategy (default)\n"
        "all-split: Merge nothing; e.g. MSSDI -> M, S, S, D, I\n"
        "all-merge: Merge adjacent non-matches; e.g. MSSDI -> M, SSDI\n"
        "all-equal: Merge adjacent same-type non-matches; e.g. MSSDI -> M, SS, D, I")
        """
        # --------------initialize 'parallel2m2'-----------------
        # self.nlp = spacy.load(os.getcwd() + "/en_core_web_sm-1.2.0/en_core_web_sm/en_core_web_sm-1.2.0")
        self.nlp = spacy.load("en_core_web_sm")
        self.args = ConfigDict(dict(lev=lev, merge=merge))
        basename = os.path.dirname(os.path.realpath(__file__))

        self.stemmer = LancasterStemmer()
        # GB English word list (inc -ise and -ize)
        self.gb_spell = toolbox.loadDictionary(basename + "/resources/en_GB-large.txt")
        # Part of speech map file
        self.tag_map = toolbox.loadTagMap(basename + "/resources/en-ptb_map")

        # --------------filter m2entries--------------------------
        self.filter_type_lst = filter_type_lst
        self.filter_token = filter_token

        # --------------lm re-rank---------------------------------
        def load_lm(lm_path, lm_databin):
            args = argparse.Namespace(
                path=lm_path, data=lm_databin,
                fp16=False, fp16_init_scale=128, fp16_scale_tolerance=0.0,
                fp16_scale_window=None, fpath=None, future_target=False,
                gen_subset='test', lazy_load=False, log_format=None, log_interval=1000,
                max_sentences=None, max_tokens=None, memory_efficient_fp16=False,
                min_loss_scale=0.0001, model_overrides='{}', no_progress_bar=True,
                num_shards=1, num_workers=0, output_dictionary_size=-1,
                output_sent=False, past_target=False,
                quiet=True, raw_text=False, remove_bpe=None, sample_break_mode=None,
                seed=1, self_target=False, shard_id=0, skip_invalid_size_inputs_valid_test=False,
                task='language_modeling', tensorboard_logdir='', threshold_loss_scale=None,
                tokens_per_sample=1024, user_dir=None, cpu=False)
            return LMScorer(args)

        self.apply_rerank = apply_rerank
        if apply_rerank:
            self.lm_scorer = load_lm(lm_path, lm_databin)
            self.preserve_spell = preserve_spell
            self.max_edits = max_edits

        # ------------LanguageTool-----------------------------
        self.apply_LT = apply_LT
        # if apply_LT:
        #     self.lang_check = language_check.LanguageTool()
        #     self.lang_check.language = 'en'
        #     self.lang_check.disabled.add('COMMA_PARENTHESIS_WHITESPACE')

        # self.noop_edit = "A -1 -1|||noop|||-NONE-|||REQUIRED|||-NONE-|||0"
        # self.too_much_edit = "A -1 -1|||too_much|||-NONE-|||REQUIRED|||-NONE-|||0"

    def _convert_coordinate(self, orig_sent, matches):
        """
        这里的matches坐标是已经排过序，需要将这个坐标转换为单词级别的
        :param orig_sent:
        :param matches:
        :return:
        """
        len_sum = 0
        # len_list = [len_sum + len(word) for word in orig_sent.split()]

        cord_list = []
        cord_list.append(0)
        for word in orig_sent.split():
            len_sum = len_sum + len(word) + 1
            cord_list.append(len_sum)

        # 写成什么复杂度的, todo, 写成什么复杂度的, 因为结束的位置不确定，所以第二个仍需要遍历完

        for match in matches:
            match_offset = match['offset']
            match_end = match_offset + match['length']
            offset_found_flag = False
            end_found_flag = False
            for i in range(len(cord_list) - 1):
                if cord_list[i] <= match_offset < cord_list[i+1]:
                    match['start'] = i
                    offset_found_flag = True
                if cord_list[i] <= match_end < cord_list[i+1]:
                    match['end'] = i + 1  # 后面是开区间
                    end_found_flag = True
                if offset_found_flag and end_found_flag:
                    break

            if match.get('end', -1) == -1:
                match['end'] = match['start'] + 1
        return matches

    # def _lt_check(self, orig_sent):
    #     matches = self.lang_check.check(orig_sent)
    #     # LT的字符级别的坐标，转换为单词级别的坐标。  LT给的offset是否
    #     # matches = self._convert_coordinate(orig_sent, matches) 全部
    #     return [[match['rule']['id'], match['rule']['category'], match['message'], (match['offset'], match['length'])] for match in matches]

    def to_m2edits(self, orig_sent, cor_sent):
        m2_edits = []
        # Markup the original sentence with spacy (assume tokenized)
        proc_orig = toolbox.applySpacy(orig_sent.split(), self.nlp)
        # Loop through the corrected sentences
        cor_sent = cor_sent.strip()
        # Identical sentences have no edits, so just write noop.
        if orig_sent == cor_sent:
            # m2_edits.append(self.noop_edit)  # 最后的数据是评卷人, 全部输入0
            return m2_edits
        # Otherwise, do extra processing.
        else:
            # Markup the corrected sentence with spacy (assume tokenized)
            proc_cor = toolbox.applySpacy(cor_sent.strip().split(), self.nlp)
            # Auto align the parallel sentences and extract the edits.
            auto_edits = align_text.getAutoAlignedEdits(proc_orig, proc_cor, self.args)
            # Loop through the edits.
            for auto_edit in auto_edits:
                # Give each edit an automatic error type.
                cat = cat_rules.autoTypeEdit(auto_edit, proc_orig, proc_cor,
                                             self.gb_spell, self.tag_map, self.nlp, self.stemmer)
                auto_edit[2] = cat
                # Write the edit to the output m2 file.
                m2_edits.append(toolbox.formatEdit(auto_edit, 0))

        return m2_edits

    def remove_m2(self, m2_edits):
        preserve_m2_edits = []
        for line in m2_edits:
            start, end, error_type, replace_token = line_to_edit(line)
            if error_type not in self.filter_type_lst:
                preserve_m2_edits.append(line)

            if self.filter_token is not None:
                if self.filter_token not in replace_token:
                    preserve_m2_edits.append(line)
        return preserve_m2_edits

    def rerank(self, sent, m2_edits):
        """仅做rerank， 不使用LT"""
        preserve_m2 = []
        rerank_m2 = []
        for line in m2_edits:
            start, end, error_type, replace_token = line_to_edit(line)
            if error_type == 'noop':
                preserve_m2.append(line)
            elif self.preserve_spell and "SPELL" in error_type:  # 是否保留拼写错误的改动,
                preserve_m2.append(line)
            else:
                rerank_m2.append(line)
        if self.max_edits is None or 0 < len(rerank_m2) < self.max_edits:
            edit_comb = get_edit_combinations(rerank_m2)  # 对所有的错误进行排列组合.

            cor_sents = []
            for e in edit_comb:
                cor = m2edits_to_cor(sent, preserve_m2 + list(e[1]))
                cor_sents.append(cor)

            score_dict = self.lm_scorer.score(cor_sents)

            min_idx = sorted(score_dict, key=score_dict.get, reverse=False)[0]
            if min_idx != 0 and -(score_dict[min_idx] - score_dict[0])/score_dict[0] > 0.02:
                sorted_m2_lines = sort_m2_lines(preserve_m2 + list(edit_comb[min_idx][1]))
            else:
                sorted_m2_lines = sort_m2_lines(preserve_m2 + list(edit_comb[0][1]))

            return [], sorted_m2_lines, []

        else:
            return [], [], []

    def rerank_with_LT(self, sent, m2_edits):
        """
        融合的问题之一是：如何解决tokenize的问题
        LanguageTool是不需要tokenize
        在融合的时候，LT使用不tokenize的
        """

        preserve_m2 = []
        rerank_m2 = []
        for line in m2_edits:
            start, end, error_type, replace_token = line_to_edit(line)
            if error_type == 'noop':
                preserve_m2.append(line)
            elif self.preserve_spell and "SPELL" in error_type:  # 是否保留拼写错误的改动,
                preserve_m2.append(line)
            else:
                rerank_m2.append(line)

        if self.max_edits is None or 0 < len(rerank_m2) < self.max_edits:
            edit_comb = get_edit_combinations(rerank_m2)  # 对所有的错误进行排列组合.

            cor_sents = []
            for e in edit_comb:
                cor = m2edits_to_cor(sent, preserve_m2 + list(e[1]))
                cor_sents.append(cor)

            lt_edits = [self._lt_check(cor_sent) for cor_sent in cor_sents]
            len_lt_edits = [len(i) for i in lt_edits]
            min_lt_edits = min(len_lt_edits)
            # Is there a better way to find a list? https://stackoverflow.com/questions/9542738/python-find-in-list
            min_lt_edits_index = [i for i, x in enumerate(len_lt_edits) if x == min_lt_edits]

            # 无法被GEC修正的错误, 但LT可以检测的. 这里也是一个list, 需要判断其中重复的内容, Bug但这个修改的坐标是不对的
            unmodifiable_lt_edits = [lt_edits[index] for index in min_lt_edits_index]
            refer_sentences = [cor_sents[index] for index in min_lt_edits_index]
            combined_unmodifiable_lt_edits = combine_unmodifiable_lt_edits(sent, refer_sentences, unmodifiable_lt_edits)

            pre_edits = [edit_comb[index] for index in min_lt_edits_index]
            # 找GEC的最小的编辑
            min_gec_edits = min(pre_edits, key=lambda t: t[0])
            golden_gec_edits = [x for i, x in pre_edits if i == min_gec_edits[0]]  # 也是combination

            if len(golden_gec_edits) > 1:
                # 说明有一种以上修改方案都可以使得LT不再检测这个错误。
                print("Multiple edits solutions")
            golden_gec_edits = list(golden_gec_edits[0])  # 如果有多个编辑方案，也只取最前面的一个

            # 仅GEC系统纠错的结果
            gec_edits = set(rerank_m2) - set(golden_gec_edits)

            # -------至此已经获取了全部编辑的三个分类：-----------------------------
            # golden_gec_edits： GEC翻译系统和LT都存在的
            # combined_unmodifiable_lt_edits: GEC系统的修改后，LT仍然可以检测. 这部分是LT单独的错误. 认为是可靠的
            # gec_edits: GEC系统单独检测到的错误.
            # ------------------------------------------------------------------

            # golden edits 已经确定， 再加上gec_edits去通过语言模型去判断剩余的
            if len(golden_gec_edits) > 0:
                edit_comb = get_edit_combinations(gec_edits)
                golden_sent = m2edits_to_cor(sent, golden_gec_edits)
                cor_sents = []
                for e in edit_comb:
                    cor = m2edits_to_cor(golden_sent, list(e[1]))
                    cor_sents.append(cor)

            score_dict = self.lm_scorer.score(cor_sents)  # 不做改变的原始句子在位置0

            min_idx = sorted(score_dict, key=score_dict.get, reverse=False)[0]  # 要score小的编辑？没有加负号
            # th = -(score_dict[min_idx] - score_dict[0]) / score_dict[0]
            # if min_idx != 0 and -(score_dict[min_idx] - score_dict[0])/score_dict[0] > 0.02:
            #     sorted_m2_lines = sort_m2_lines(preserve_m2 + golden_gec_edits + list(edit_comb[min_idx][1]))
            # else:
            #     sorted_m2_lines = sort_m2_lines(preserve_m2 + golden_gec_edits + list(edit_comb[0][1]))
            # sorted_m2_lines = sort_m2_lines(preserve_m2 + golden_gec_edits + list(edit_comb[min_idx][1]))
            # if len(sorted_m2_lines) == 0:
            #     sorted_m2_lines.append(self.noop_edit)
            return golden_gec_edits, list(edit_comb[min_idx][1]), combined_unmodifiable_lt_edits   # 将golden_gec_edits也传出去
        elif len(rerank_m2) == 0:
            # output_entries.append(m2_entry)  # too much errors, just alert the users, we do not change the sentences
            lt_edits = self._lt_check(sent)
            return [], [], lt_edits
        else:
            lt_edits = self._lt_check(sent)
            return [], [], lt_edits  # error > max_edits 错误太多的，就直接返回

    def process(self, ori, cor):
        """
        将几个处理总的联合起来
        :param ori:
        :param cor:
        :return:
        """
        edits = self.to_m2edits(ori, cor)
        edits = self.remove_m2(edits)
        if self.apply_LT and self.apply_rerank:
            return self.rerank_with_LT(ori, edits)
        if self.apply_rerank:
            return self.rerank(ori, edits)
        return [], edits, []


class ConfigDict(Dict):

    def __missing__(self, name):
        raise KeyError(name)

    def __getattr__(self, name):
        try:
            value = super(ConfigDict, self).__getattr__(name)
        except KeyError:
            ex = AttributeError("'{}' object has no attribute '{}'".format(
                self.__class__.__name__, name))
        except Exception as e:
            ex = e
        else:
            return value
        raise ex


def combine_unmodifiable_lt_edits(ori_sentence, refer_sentences, unmodifiable_lt_edits):
    # todo: 是否有出现不一样的可能
    unmodifiable_lt_edit = unmodifiable_lt_edits[0]
    refer_sentence = refer_sentences[0]
    # for refer_sentence, unmodifiable_lt_edit in zip(refer_sentences, unmodifiable_lt_edits):
    #     # 原句，[ [], []]
    #     for edit in unmodifiable_lt_edits:
    #
    #         pass
    # return unmodifiable_lt_edits[0]
    combined_lt_edit = []
    for edit in unmodifiable_lt_edit:
        start, offset = edit[3]
        match_str = refer_sentence[start:start + offset]
        start = ori_sentence.find(match_str)
        if start > 0:
            edit[3] = (start, offset)
            combined_lt_edit.append(edit)
    return combined_lt_edit


def line_to_edit(m2_line):
    if not m2_line.startswith("A"):
        return None
    features = m2_line.split("|||")
    span = features[0].split()
    start, end = int(span[1]), int(span[2])
    error_type = features[1]
    replace_token = features[2]
    return start, end, error_type, replace_token


def get_edit_combinations(edits):
    edit_combinations = []
    for i in range(len(edits) + 1):
        edit_combinations.extend( [(i, combine_edits) for combine_edits in combinations(edits, i)] )  # 记录有几个edits

    return edit_combinations


def sort_m2_lines(m2_lines):
    m2_dict = dict()
    for line in m2_lines:
        s, _, _, _ = line_to_edit(line)
        m2_dict[s] = line
    return [i[1] for i in sorted(m2_dict.items())]


def m2edits_to_cor(ori, m2_lines):
    _m2_lines = sort_m2_lines(m2_lines)

    skip = {"noop", "UNK", "Um"}
    cor_sent = ori.split()

    offset = 0
    for edit in _m2_lines:
        edit = edit.split("|||")
        if edit[1] in skip: continue  # Ignore certain edits
        span = edit[0].split()[1:]  # Ignore "A "
        start = int(span[0])
        end = int(span[1])
        cor = edit[2].split()
        cor_sent[start + offset:end + offset] = cor
        offset = offset - (end - start) + len(cor)
    return " ".join(cor_sent)


if __name__ == '__main__':
    """
    filter_token=None, filter_type_lst=[],
                 lev=True, merge='rules',
                 apply_rerank=False, lm_path=None, lm_databin=None,
                 preserve_spell=False, max_edits=7,
    """

    # lm_path = f"/media/Data/wangjunjie_code/fairseq_gec_Kakao/data/language_model/wiki103.pt"
    # lm_databin = f"/media/Data/wangjunjie_code/fairseq_gec_Kakao/data/language_model/data-bin"

    # filter = M2Filter(filter_type_lst=['U:CONJ', 'U:VERB:FORM', 'U:ADV',
    #                                       'M:ADJ', 'R:OTHER', 'R:NOUN', 'U:VERB', 'U:OTHER', 'U:NOUN'],
    #                  apply_rerank=False,
    #                  apply_LT=False,
    #                  lm_path=lm_path,
    #                  lm_databin=lm_databin
    #                  )
    # ori = 'I will appreciated it if you correct my sentences . Please call me for you convenience , my phone number is 2333333 .'
    # cor = 'I would appreciate it if you could correct my sentences . Please call me for you convenience , my phone number is 2333333 .'
    # ori = 'Everyone must join sports competitions .'
    # cor = 'Everyone must enter sports competitions .'

    #edits = filter.process(ori, cor)
    pass
