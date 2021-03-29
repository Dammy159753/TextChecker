import json

sentence = {
        "source": "I'm not a vegetarian my self, but I have many friends who are vegetarians or even vegans.",
        "ori": "I 'm not a vegetarian my self , but I have many friends who are vegetarians or even vegans .", 
        "cor": "I 'm not a vegetarian myself , but I have many friends who are vegetarians or even vegans .",
        "edits": ["A 5 7|||R:ORTH|||myself|||REQUIRED|||-NONE-|||0"]
    }
sentence = {
        "source": "Hi, I'm this men do school's hand teacher -Mr. You.",
        "ori": "Hi , I 'm this men do school 's hand teacher -Mr. You .", 
        "cor": "Hi , I 'm this man doing school 's hand teacher -Mr. You .", 
        "edits": ["A 5 6|||R:NOUN:NUM|||man|||REQUIRED|||-NONE-|||0", "A 6 7|||R:VERB:FORM|||doing|||REQUIRED|||-NONE-|||0"]
    }


def get_cha_position(edits, word_token):
    # edits = list(sentence['edits'])
    # word_token = sentence['ori'].split(' ')
    gec_edits = list()
    for edit in edits:
        edit_split = edit.split('|||')[0].split(' ')
        gec_start_token = int(edit_split[1])
        gec_end_token = int(edit_split[2])
        if gec_start_token > 0:
            gec_start_index = len(' '.join(word_token[0: gec_start_token])) + 1
        else:
            gec_start_index = 0
        if gec_start_token == gec_end_token:
            gec_end_index = gec_start_index
        else:
            gec_end_index = len(' '.join(word_token[0: gec_end_token]))
        gec_edits.append({
            'gec_start': gec_start_index,
            'gec_end': gec_end_index
        })
    # print('gec_edits: ', gec_edits)
    return gec_edits


def get_space_position(source, ori):
    # source = sentence['source']
    # ori = sentence['ori']
    space_position = list()
    for i in range(len(ori)):
        if source[0:i] != ori[0:i]:
            space_position.append(i)
            source_list = list(source)
            source_list.insert(i - 1, ' ')
            source = ''.join(source_list)
    # print('space_position', space_position)
    return space_position


def get_source_edits(gec_edits, space_position):

    for edit in gec_edits:
        edit['offset'] = edit['offset_token']

    for i, position in enumerate(space_position):
        for edit in gec_edits:
            if edit['offset_token'] > position:
                edit['offset'] = edit['offset_token'] - i - 1

    # print('source_edits: ', gec_edits)
    return gec_edits


def convert(gec_edits, source, tokenized_source):
    space_position = get_space_position(source, tokenized_source)
    source_edits = get_source_edits(gec_edits, space_position)
    return source_edits