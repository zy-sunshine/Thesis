import os
import cmmseg
import sys
sys.path.insert(0, "pymmseg-cpp")
import mmseg
class Tokenizer():
    def __init__(self, token_method):
        self.token_list = []
        self.token_method = token_method
    def set_segments(self, *segs):
        self.segments = segs
        self.length = len(self.segments)
    def do_tokenized(self):
        for seg in self.segments:
            self.token_list.append(self.token_method(seg))
class TokenizerCmmseg(Tokenizer):
    def __init__(self, dict_etc_path="/usr/local/coreseek/dict"):
        cmmseg.init(dict_etc_path)
        Tokenizer.__init__(self, cmmseg.segment)

    def set_segments(self, *segs):
        self.segments = segs
        self.length = len(self.segments)

    def get_tokens(self):
        self.do_tokenized()
        #res = []
        #for token in self.token_list:
        #    res.append(token)
        return self.token_list

class TokenizerPymmsegcpp(Tokenizer):
    def __init__(self, dict_chars=None, dict_words=None):
        if dict_chars:
            mmseg.mmseg_load_chars(dict_chars)
        elif dict_words:
            mmseg.mmseg_load_words(dict_words)
        else:
            mmseg.dict_load_defaults()
        Tokenizer.__init__(self, mmseg.Algorithm)

    def get_tokens(self):
        self.do_tokenized()
        res = []
        for token in self.token_list:
            tok_each = []
            for tok in token:
                tok_each.append(tok.text)
            res.append(tok_each)
        return res

def count_terms(terms, term_map, charset):
    tmp_map = {}
    for term in terms:
        if tmp_map.has_key(term):
            tmp_map[term] += 1
        else:
            tmp_map[term] = 1
    for term, count in tmp_map.iteritems():
        term_map[term.decode(charset)] = count

#for key, value in term_sub_map.iteritems():
#    print key ,value, len(key)
def get_top_terms(term_map):
    term_list = filter(lambda k: len(k[0])>1, term_map.iteritems())
    keywords = sorted(term_list, key=lambda d:d[1], reverse = True )
    return keywords



def get_keywords(subject, message, tokenizer, charset = "utf8"):
    tokenizer.set_segments(subject, message)
    term_sub, term_msg = tokenizer.get_tokens()
    
    term_sub_map = {}
    term_msg_map = {}

    count_terms(term_sub, term_sub_map, charset)
    count_terms(term_msg, term_msg_map, charset)
    sub_keywords = get_top_terms(term_sub_map)
    msg_keywords = get_top_terms(term_msg_map)
    # Select all keywords in subject and 5 keywords from message 
    # as the keywords set.
    keywords = sub_keywords[:]
    keywords.extend(msg_keywords[:5])
    return keywords, len(sub_keywords)


    return
if __name__ == '__main__':
    f = open("text1.txt")
    subject = f.readline()
    #message = f.readlines()
    message = f.read()

    tokenizer = TokenizerCmmseg()
    #tokenizer = TokenizerPymmsegcpp()
    keywords, sub_tok_len = get_keywords(subject, message, tokenizer)

    for key, count in keywords:
        print key, count, len(key)
