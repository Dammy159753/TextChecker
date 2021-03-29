config = dict(
    gec_config=dict(
        data=['english_check/GEC_check/gec_data'],
        path='/model/checkpoint6.pt',
        beam=12,
        nbest=1,
        target_lang='tgt',
        source_lang='src',
        buffer_size=16,  # 批处理的参数, 其实只有max_sentences有用
        max_sentences=16,
        copy_ext_dict=True,
        replace_unk=True),
    post_process_config=dict(
        filter_token=None,
        filter_type_lst= ['M:OTHER','M:PART','M:CONJ','M:DET','M:NOUN','M:NOUN:POSS','M:PREP','M:PRON','M:PUNCT','M:VERB:FORM','M:ADJ','M:ADV','R:CONJ','R:ADJ','R:ADV','R:OTHER', 'R:NOUN','R:NOUN:POSS','R:NOUN:INFL', 'R:VERB','R:PART','R:PREP','R:PUNCT','R:VERB:TENSE','R:CONTR','R:WO','R:MORPH', 'U:OTHER', 'U:PUNCT','U:CONJ','U:CONTR','U:NOUN:POSS','U:PREP','U:PRON','U:DET','U:VERB:FORM','U:ADV','U:ADJ','U:NOUN'], # 过滤掉的错误类型
        lev=True, merge='rules',
        apply_LT=False,
        apply_rerank=False,
        preserve_spell=False,
        max_edits=5,  # 当一句话检测到的错误多余这个的时候，将不再返回
    )
)
