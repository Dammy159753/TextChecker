from Faspell.char_sim import CharFuncs
from Faspell.masked_lm import MaskedLM
from bert_modified import modeling
import re
import json
import pickle
import argparse
import numpy
import logging
import plot
from tqdm import tqdm
import time
from logserver import log_server
####################################################################################################

__author__ = 'Yuzhong Hong <hongyuzhong@qiyi.com / eugene.h.git@gmail.com>'
__date__ = '10/09/2019'
__description__ = 'The main script for FASPell - Fast, Adaptable, Simple, Powerful Chinese Spell Checker'


CONFIGS = json.loads(open('Faspell/faspell_configs.json', 'r', encoding='utf-8').read())

WEIGHTS = (CONFIGS["general_configs"]["weights"]["visual"], CONFIGS["general_configs"]["weights"]["phonological"], 0.0)

CHAR = CharFuncs(CONFIGS["general_configs"]["char_meta"])


class LM_Config(object):

    vocab_file = CONFIGS["general_configs"]["lm"]["vocab"]
    bert_config_file = CONFIGS["general_configs"]["lm"]["bert_configs"]
    bert_config = modeling.BertConfig.from_json_file(bert_config_file)
    topn = CONFIGS["general_configs"]["lm"]["top_n"]


class Filter(object):
    def __init__(self):
        self.curve_idx_sound = {
            0: {0: Curves.curve_null,  # 0 for non-difference
                1: Curves.curve_null,
                2: Curves.curve_null,
                3: Curves.curve_null,
                4: Curves.curve_null,
                5: Curves.curve_null,
                6: Curves.curve_null,
                7: Curves.curve_null,
                },
            1: {0: Curves.curve_01,  # 1 for difference
                1: Curves.curve_01,
                2: Curves.curve_01,
                3: Curves.curve_01,
                4: Curves.curve_01,
                5: Curves.curve_01,
                6: Curves.curve_01,
                7: Curves.curve_01,
                }
        }
        self.curve_idx_shape = {0: {0: Curves.curve_null,  # 0 for non-difference
                                    1: Curves.curve_null,
                                    2: Curves.curve_null,
                                    3: Curves.curve_null,
                                    4: Curves.curve_null,
                                    5: Curves.curve_null,
                                    6: Curves.curve_null,
                                    7: Curves.curve_null,
                                    },
                                1: {0: Curves.curve_01,  # 1 for difference
                                    1: Curves.curve_01,
                                    2: Curves.curve_01,
                                    3: Curves.curve_01,
                                    4: Curves.curve_01,
                                    5: Curves.curve_01,
                                    6: Curves.curve_01,
                                    7: Curves.curve_01,
                                    }}

    def filter(self, rank, difference, error, filter_is_on=True, sim_type='shape'):
        if filter_is_on:
            if sim_type == 'sound':
                curve = self.curve_idx_sound[int(difference)][rank]
            else:
                curve = self.curve_idx_shape[int(difference)][rank]
        else:
            curve = Curves.curve_null
        if curve(error["confidence"], error["similarity"]) and self.special_filters(error):
            return True
        return False

    @staticmethod
    def special_filters(error):
        """
        Special filters for, essentially, grammatical errors. The following is some examples.
        """
        # if error["original"] in {'他': 0, '她': 0, '你': 0, '妳': 0}:
        #     if error["confidence"] < 0.95:
        #         return False
        #
        # if error["original"] in {'的': 0, '得': 0, '地': 0}:
        #     if error["confidence"] < 0.6:
        #         return False
        #
        # if error["original"] in {'在': 0, '再': 0}:
        #     if error["confidence"] < 0.6:
        #         return False

        return True


class Curves(object):
    def __init__(self):
        pass

    @staticmethod
    def curve_null(confidence, similarity):
        """This curve is used when no filter is applied"""
        return True

    @staticmethod
    def curve_full(confidence, similarity):
        """This curve is used to filter out everything"""
        return False

    @staticmethod
    def curve_01(confidence, similarity):
        """
        we provide an example of how to write a curve. Empirically, curves are all convex upwards.
        Thus we can approximate the filtering effect of a curve using its tangent lines.
        """
        flag1 = 20 / 3 * confidence + similarity - 21.2 / 3 > 0
        flag2 = 0.2 * confidence + similarity - 0.7 > 0
        if flag1 or flag2:
            return True
        return False


class SpellChecker(object):
    def __init__(self, model_path, max_length):
        self.masked_lm = MaskedLM(LM_Config(),model_path, max_length)
        self.filter = Filter()

    @staticmethod
    def pass_ad_hoc_filter(corrected_to, original):
        if corrected_to == '[UNK]':
            return False
        if '#' in corrected_to:
            return False
        if len(corrected_to) != len(original):
            return False
        if re.findall(r'[a-zA-ZＡ-Ｚａ-ｚ]+', corrected_to):
            return False
        if re.findall(r'[a-zA-ZＡ-Ｚａ-ｚ]+', original):
            return False
        return True

    def get_error(self, sentence, j, cand_tokens, rank=0, difference=True, filter_is_on=True, weights=WEIGHTS, sim_type='shape'):
        """
        PARAMS
        ------------------------------------------------
        sentence: sentence to be checked
        j: position of the character to be checked
        cand_tokens: all candidates
        rank: the rank of the candidate in question
        filters_on: only used in ablation experiment to remove CSD
        weights: weights for different types of similarity
        sim_type: type of similarity

        """

        cand_token, cand_token_prob = cand_tokens[rank]

        # if cand_token != sentence[j]:
        error = {
            "error_position": j,
            "original": sentence[j],
            "corrected_to": cand_token,
            "candidates": dict(cand_tokens),
            "confidence": cand_token_prob,
            "similarity": CHAR.similarity(sentence[j], cand_token, weights=weights),
            "sentence_len": len(sentence)
        }
        if not self.pass_ad_hoc_filter(error["corrected_to"], error["original"]):
            return None
        else:
            if self.filter.filter(rank, difference, error, filter_is_on, sim_type=sim_type):
                return error
            return None
        # return None

    def make_corrections(self,
                         sentences,
                         tackle_n_gram_bias=CONFIGS["exp_configs"]["tackle_n_gram_bias"],
                         rank_in_question=CONFIGS["general_configs"]["rank"],
                         dump_candidates=CONFIGS["exp_configs"]["dump_candidates"],
                         read_from_dump=CONFIGS["exp_configs"]["read_from_dump"],
                         filter_is_on=CONFIGS["exp_configs"]["filter_is_on"],
                         is_train=False,
                         train_on_difference=True,
                         sim_union=CONFIGS["exp_configs"]["union_of_sims"]
                         ):
        """
        PARAMS:
        ------------------------------
        sentences: sentences with potential errors
        tackle_n_gram_bias: whether the hack to tackle n gram bias is used
        rank_in_question: rank of the group of candidates in question
        dump_candidates: whether save candidates to a specific path
        read_from_dump: read candidates from dump
        is_train: if the script is in the training mode
        train_on_difference: choose the between two sub groups
        filter_is_on: used in ablation experiments to decide whether to remove CSD
        sim_union: whether to take the union of the filtering results given by using two types of similarities

        RETURN:
        ------------------------------
        correction results of all sentences
        """
        processed_sentences = self.process_sentences(sentences)
        if read_from_dump:
            assert dump_candidates
            topn_candidates = pickle.load(open(dump_candidates, 'rb'))
        else:
            topn_candidates = self.masked_lm.find_topn_candidates(processed_sentences,
                                                                  batch_size=CONFIGS["general_configs"]["lm"]["batch_size"])
            if dump_candidates:
                pickle.dump(topn_candidates, open(dump_candidates, 'wb'))

        # main workflow
        skipped_count = 0
        results = []
        # if logging.getLogger().getEffectiveLevel() != logging.INFO:  # show progress bar if not in verbose mode
        #     progess_bar = tqdm.tqdm(enumerate(topn_candidates))
        # else:
        progess_bar = enumerate(topn_candidates)

        for i, cand in progess_bar:
            if i < len(sentences):
                sentence = ''
                res = []

                # can't cope with sentences containing Latin letters yet.
                if re.findall(r'[a-zA-ZＡ-Ｚａ-ｚ]+', sentences[i]):
                    skipped_count += 1
                    results.append({"original_sentence": sentences[i],
                                    "corrected_sentence": sentences[i],
                                    "num_errors": 0,
                                    "errors": []
                                    })
                else:
                    # when testing on SIGHAN13,14,15, we recommend using `extension()` to solve
                    # issues caused by full-width humbers;
                    # when testing on OCR data, we recommend using `extended_cand = cand`
                    extended_cand = extension(cand)
                    for j, cand_tokens in enumerate(extended_cand):  # spell check for each characters
                        if (0 < j < len(extended_cand) - 1) &(j<len(sentences[i])):  # skip the head and the end placeholders -- `。`
                            char = sentences[i][j - 1]
                            # detect and correct errors
                            max_error = None

                            # spell check rank by rank
                            for rank in range(rank_in_question + 1):
                                if WEIGHTS[0] > WEIGHTS[1]:
                                    sim_type = 'shape'
                                else:
                                    sim_type = 'sound'
                                error = self.get_error(sentences[i],
                                                       j - 1,
                                                       cand_tokens,
                                                       rank=rank,
                                                       difference=cand_tokens[0][0] != sentences[i][j - 1],
                                                       filter_is_on=filter_is_on, sim_type=sim_type)
                                if not max_error:
                                    max_error = error
                                else:
                                    if error:
                                        if error['similarity'] > max_error['similarity']:
                                            max_error = error

                            if max_error and max_error['original'] != max_error['corrected_to']:
                                res.append(max_error)
                                char = max_error['corrected_to']
                                sentence += char
                                continue
                            sentence += char

                    # a small hack: tackle the n-gram bias problem: when n adjacent characters are erroneous,
                    # pick only the one with the greatest confidence.
                    error_delete_positions = []
                    if tackle_n_gram_bias:
                        error_delete_positions = []
                        for idx, error in enumerate(res):
                            delta = 1
                            n_gram_errors = [error]
                            try:
                                while res[idx + delta]["error_position"] == error["error_position"] + delta:
                                    n_gram_errors.append(res[idx + delta])
                                    delta += 1
                            except IndexError:
                                pass
                            n_gram_errors.sort(key=lambda e: e["confidence"], reverse=True)
                            error_delete_positions.extend([(e["error_position"], e["original"]) for e in n_gram_errors[1:]])

                        error_delete_positions = dict(error_delete_positions)

                        res = [e for e in res if e["error_position"] not in error_delete_positions]

                        def process(pos, c):
                            if pos not in error_delete_positions:
                                return c
                            else:
                                return error_delete_positions[pos]
                        sentence = ''.join([process(pos, c) for pos, c in enumerate(sentence)])
                    # add the result for current sentence
                    results.append({"original_sentence": sentences[i],
                                    "corrected_sentence": sentence,
                                    "num_errors": len(res),
                                    "errors": res})
        return results

    def repeat_make_corrections(self, sentences, num=3, is_train=False, train_on_difference=True):
        all_results = []
        sentences_to_be_corrected = sentences

        for _ in range(num):
            results = self.make_corrections(sentences_to_be_corrected,
                                            is_train=is_train,
                                            train_on_difference=train_on_difference)
            sentences_to_be_corrected = [res["corrected_sentence"] for res in results]
            all_results.append(results)

        correction_history = []

        for i, sentence in enumerate(sentences):
            r = {"original_sentence": sentence, "correction_history": []}
            for item in all_results:
                r["correction_history"].append(item[i]["corrected_sentence"])
            correction_history.append(r)

        return all_results, correction_history

    @staticmethod
    def process_sentences(sentences):
        """Because masked language model is trained on concatenated sentences,
         the start and the end of a sentence in question is very likely to be
         corrected to the period symbol (。) of Chinese. Hence, we add two period
        symbols as placeholders to prevent this from harming FASPell's performance."""
        return ['。' + sent + '。' for sent in sentences]


def extension(candidates):
    """this function is to resolve the bug that when two adjacent full-width numbers/letters are fed to mlm,
       the output will be merged as one output, thus lead to wrong alignments."""
    new_candidates = []
    for j, cand_tokens in enumerate(candidates):
        real_cand_tokens = cand_tokens[0][0]
        if '##' in real_cand_tokens:  # sometimes the result contains '##', so we need to get rid of them first
            real_cand_tokens = real_cand_tokens[2:]

        if len(real_cand_tokens) == 2 and not re.findall(r'[a-zA-ZＡ-Ｚａ-ｚ]+', real_cand_tokens):
            a = []
            b = []
            for cand, score in cand_tokens:
                real_cand = cand
                if '##' in real_cand:
                    real_cand = real_cand[2:]
                a.append((real_cand[0], score))
                b.append((real_cand[-1], score))
            new_candidates.append(a)
            new_candidates.append(b)
            continue
        new_candidates.append(cand_tokens)

    return new_candidates




if __name__ == '__main__':
    SpellChecker()