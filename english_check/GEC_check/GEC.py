"""
Translate raw text with a trained model. Batches data on-the-fly.
"""

import logging
logging.basicConfig(level = logging.INFO,format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename="gec.log")
logger = logging.getLogger(__name__)
from collections import namedtuple
import numpy as np
import sys
import codecs
import torch
import re
from tqdm import tqdm
from nltk.tokenize import word_tokenize
from nltk.tokenize.treebank import TreebankWordDetokenizer
from fairseq import data, options, tasks, tokenizer, utils
from fairseq.sequence_generator import SequenceGenerator


Batch = namedtuple('Batch', 'ids src_tokens src_lengths, src_strs')
Translation = namedtuple('Translation', 'src_str hypos pos_scores alignments')


class GECModel(object):
    def __init__(self, args):
        self.args = args
        self.detokenizer = TreebankWordDetokenizer()

        if args.buffer_size < 1:
            args.buffer_size = 1
        if args.max_tokens is None and args.max_sentences is None:
            args.max_sentences = 1

        assert not args.sampling or args.nbest == args.beam, \
            '--sampling requires --nbest to be equal to --beam'
        assert not args.max_sentences or args.max_sentences <= args.buffer_size, \
            '--max-sentences/--batch-size cannot be larger than --buffer-size'

        print(args)

        self.use_cuda = torch.cuda.is_available() and not args.cpu


        # Setup task, e.g., translation
        task = tasks.setup_task(args)  # 注册的任务

        # Load ensemble
        print('| loading model(s) from {}'.format(args.path))
        self.models, _model_args = utils.load_ensemble_for_inference(
            args.path.split(':'), task, model_arg_overrides=eval(args.model_overrides),
        )

        args.copy_ext_dict = getattr(_model_args, "copy_attention", False)  # copy mechanism独有

        # Set dictionaries
        self.tgt_dict = task.target_dictionary
        self.src_dict = task.source_dictionary

        # Optimize ensemble for generation
        for model in self.models:
            model.make_generation_fast_(
                beamable_mm_beam_size=None if args.no_beamable_mm else args.beam,
                need_attn=args.print_alignment,
            )
            if args.fp16:
                model.half()
            if self.use_cuda:
                model.cuda()

        # Initialize generator
        self.generator = task.build_generator(args)

        # Load alignment dictionary for unknown word replacement
        # (None if no unknown word replacement, empty if no path to align dictionary)
        self.align_dict = utils.load_align_dict(args.replace_unk)
        if self.align_dict is None and args.copy_ext_dict:
            self.align_dict = {}

        self.max_positions = utils.resolve_max_positions(
            task.max_positions(),
            *[model.max_positions() for model in self.models]
        )

        if args.buffer_size > 1:
            print('| Sentence buffer size:', args.buffer_size)
        self.task = task

    def make_result(self, src_str, hypos):
        result = Translation(
            src_str='O\t{}'.format(src_str),
            hypos=[],
            pos_scores=[],
            alignments=[],
        )

        # Process top predictions
        for hypo in hypos[:min(len(hypos), self.args.nbest)]:
            hypo_tokens, hypo_str, alignment = utils.post_process_prediction(
                hypo_tokens=hypo['tokens'].int().cpu(),
                src_str=src_str,
                alignment=hypo['alignment'].int().cpu() if hypo['alignment'] is not None else None,
                align_dict=self.align_dict,
                tgt_dict=self.tgt_dict,
                remove_bpe=self.args.remove_bpe,
            )
            result.hypos.append('H\t{}\t{}'.format(hypo['score'], hypo_str))
            result.pos_scores.append('P\t{}'.format(
                ' '.join(map(
                    lambda x: '{:.4f}'.format(x),
                    hypo['positional_scores'].tolist(),
                ))
            ))
            result.alignments.append(
                'A\t{}'.format(' '.join(map(lambda x: str(utils.item(x)), alignment)))
                if self.args.print_alignment else None
            )
        return result

    def process_batch(self, batch):
        tokens = batch.tokens
        lengths = batch.lengths

        if self.use_cuda:
            tokens = tokens.cuda()
            lengths = lengths.cuda()

        encoder_input = {'src_tokens': tokens, 'src_lengths': lengths}
        translations = self.generator.generate(
            encoder_input,
            maxlen=int(self.args.max_len_a * tokens.size(1) + self.args.max_len_b),
        )

        return [self.make_result(batch.srcs[i], t) for i, t in enumerate(translations)]

    @staticmethod
    def get_modified(text, errors):
        # errors中的坐标已经经过了排序
        words = text.split()
        # 加中括号， 不要颜色了
        modified = []

        start_posi = 0
        for error in errors:
            # error字段
            # Nn||sub||20||21||country
            #
            # 前面无修改的部分
            modified.append(' '.join(words[start_posi:int(error[2])]))
            # 有修改的部分
            modified.append('[' + error[0] + ':')
            modified.append(' '.join(words[int(error[2]):int(error[3])]))  # 原句  若是增加的话， 这里是空
            modified.append('-->')  # 箭头标记
            modified.append(error[4])  # 若是删除的话，这里为空
            modified.append(']')
            start_posi = int(error[3])

        if start_posi < len(words):
            modified.append(' '.join(words[start_posi:]))

        return ' '.join(modified)

    def infer(self, sentences):
        """

        :param sentences: should be a list, and tokenized
        :return:
        """
        # logger.info('allocated_mem:{}'.format(torch.cuda.memory_allocated()))
        # logger.info('cached_mem:{}'.format(torch.cuda.memory_cached()))
        if len(sentences) < 1:
            return ''
        start_id = 0
        src_strs = sentences
        results = []
        for batch in self.make_batches(sentences, self.args, self.task, self.max_positions):
            src_tokens = batch.src_tokens
            src_lengths = batch.src_lengths
            # src_strs.extend(batch.src_strs)
            if self.use_cuda:
                src_tokens = src_tokens.cuda()
                src_lengths = src_lengths.cuda()

            sample = {
                'net_input': {
                    'src_tokens': src_tokens,
                    'src_lengths': src_lengths,
                },
            }
            translations = self.task.inference_step(self.generator, self.models, sample)
            for i, (id, hypos) in enumerate(zip(batch.ids.tolist(), translations)):
                src_tokens_i = utils.strip_pad(src_tokens[i], self.tgt_dict.pad())
                results.append((start_id + id, src_tokens_i, hypos))

        # sort output to match input order
        trg_lines = []
        index = 0
        for id, src_tokens, hypos in sorted(results, key=lambda x: x[0]):
            # if self.src_dict is not None:
            #     src_str = self.src_dict.string(src_tokens, self.args.remove_bpe)
            # Process top predictions
            for hypo in hypos[:min(len(hypos), self.args.nbest)]:
                hypo_tokens, hypo_str, alignment = utils.post_process_prediction(
                    hypo_tokens=hypo['tokens'].int().cpu(),
                    src_str=src_strs[id],  # 这个source 原来传得不对src_strs怎么被排序了
                    alignment=hypo['alignment'].int().cpu() if hypo['alignment'] is not None else None,
                    align_dict=self.align_dict,
                    tgt_dict=self.tgt_dict,
                    remove_bpe=self.args.remove_bpe,
                )
                # 卡置信度阈值
                if hypo['score'] > -0.1:
                    # print('H-{}\t{}\t{}'.format(id, hypo['score'], hypo_str))
                    trg_lines.append(hypo_str)
                else:
                    # print(sentences[index])
                    trg_lines.append(sentences[index])
                index += 1
        torch.cuda.empty_cache()
        return trg_lines

    @staticmethod
    def make_batches(lines, args, task, max_positions):
        tokens = [
            task.source_dictionary.encode_line(src_str, add_if_not_exist=False, copy_ext_dict=args.copy_ext_dict).long()
            for src_str in lines
        ]
        lengths = torch.LongTensor([t.numel() for t in tokens])
        itr = task.get_batch_iterator(
            dataset=task.build_dataset_for_inference(tokens, lengths),
            max_tokens=args.max_tokens,
            max_sentences=args.max_sentences,
            max_positions=max_positions,
        ).next_epoch_itr(shuffle=False)
        for batch in itr:
            yield Batch(
                ids=batch['id'],
                src_tokens=batch['net_input']['src_tokens'], src_lengths=batch['net_input']['src_lengths'],
                src_strs=[lines[i] for i in batch['id']],
            )


if __name__ == '__main__':

    # from config import GEC_config
    from config import config

    parser = options.get_generation_parser(interactive=True)
    args = options.parse_args_and_arch(parser)
    args_dict = vars(args)
    # for key in GEC_config:
    #     args_dict[key] = GEC_config[key]
    for key in config['gec_config']:
        args_dict[key] = config['gec_config'][key]
    gec = GECModel(args)

    # 批量测试的时候，这句话
    src = ["Travel by bus is exspensive , bored and annoying .",
           "I am sorry to tell you that I could n't join in the speech , which about English famous writers .",
           'I had gotten an e-mail from my parents last night , which said that they would returned home in Sunday morning .',
           'My parents have been staying in America for a year .',
           "During this year , I miss them every day , so I ca n't wait to see them .",
           'Be- cause of that , my schedule of Sunday is full for my parents .',
           "I 'm regret to tell you that , but I desire to get the knowledge about English authors and writers .",
           'So I hope you can send me the information of the speech .',
           'Besides , I would like to invite you to join in a speech with me .',
           'Please call me for you convenience , my phone number is 2333333 .']
    trg_lines = gec.infer(src)
    pass
