#!/usr/bin/python
# -*- coding=utf-8 -*-
import sys
from math import log, sqrt
from itertools import combinations
sys.path.insert(0,
        "/home/sunshine/Thesis/django-website/clusterweb/searchengine")
from LinuxFansSql import LinuxFansMysql
from getkeywords import TokenizerCmmseg, get_keywords
import types
# The tokenizer cannot initial multi times in local function.
tokenizer = TokenizerCmmseg()

def cosine_distance(a, b):
    cos = 0.0
    a_tfidf = a["tfidf"]
    for token, tfidf in b["tfidf"].iteritems():
        if token in a_tfidf:
            cos += tfidf * a_tfidf[token]
    return cos

def normalize(features):
    if not features:
        return features
    if type(features) == types.DictType:
        norm = 1.0 / sqrt(sum(i**2 for i in features.itervalues()))
        for k, v in features.iteritems():
            features[k] = v * norm
    elif type(features) == types.ListType:
        norm = 1.0 / sqrt(sum(i**2 for i in features))
        for i in range(len(features)):
            features[i] = features[i] * norm
    return features

def add_tfidf_to_old(documents):
    tokens = {}
    for id, doc in enumerate(documents):
        tf = {}
        doc["tfidf"] = {}
        doc_tokens = doc.get("tokens", [])
        for token in doc_tokens:
            tf[token] = tf.get(token, 0) + 1
        num_tokens = len(doc_tokens)
        if num_tokens > 0:
            for token, freq in tf.iteritems():
                tokens.setdefault(token, []).append((id, float(freq) / num_tokens))

    doc_count = float(len(documents))
    for token, docs in tokens.iteritems():
        idf = log(doc_count / len(docs))
        for id, tf in docs:
            tfidf = tf * idf
            if tfidf > 0:
                documents[id]["tfidf"][token] = tfidf

    for doc in documents:
        doc["tfidf"] = normalize(doc["tfidf"])

def add_tfidf_to(documents_format):
    documents, tokens_appear_map, doc_terms_count = documents_format
    tokens = {}
    for id, doc in enumerate(documents):
        doc["tfidf"] = {}

        docid = doc["docid"]
        token_list = doc["token_list"]
        token_map = doc["token_map"]

        terms_count = doc_terms_count[docid]
        if terms_count > 0:
            for tok in token_list:
                token_freq = token_map[tok]["count"]
                tokens.setdefault(tok, []).append((id, float(token_freq) / terms_count))

    doc_count = float(len(documents))
    for token, docs in tokens.iteritems():
        # Notice: len(docs) == len(tokens_appear_map[token]) should be True
        idf = log(doc_count / len(docs))
        for id, tf in docs:
            tfidf = tf * idf
            if tfidf > 0:
                documents[id]["tfidf"][token] = tfidf
    for doc in documents:
        doc["tfidf"] = normalize(doc["tfidf"])
            
def choose_cluster(node, cluster_lookup, edges):
    new = cluster_lookup[node]
    if node in edges:
        seen, num_seen = {}, {}
        for target, weight in edges.get(node, []):
            # node 与 target 所属类的相似性(以到 target 类的 cosine 累加值来计算)
            seen[cluster_lookup[target]] = seen.get(
                cluster_lookup[target], 0.0) + weight
        for k, v in seen.iteritems():
            num_seen.setdefault(v, []).append(k)
        # 相似度越大越应被归为一类
        max_num = max(num_seen)
        if max_num <= 0:
            # 如果与所有类的相关度都不大与 0, 则不分类
            pass
        else:
            new = num_seen[max(num_seen)][0]
    return new

def majorclust(graph):
    # node 所属类查询字典
    cluster_lookup = dict((node, i) for i, node in enumerate(graph.nodes))

    count = 0
    movements = set()
    finished = False
    while not finished:
        finished = True
        #print cluster_lookup
        #print movements
        for node in graph.nodes:
            new = choose_cluster(node, cluster_lookup, graph.edges)
            move = (node, cluster_lookup[node], new)
            #print "Move %s to %s" % (cluster_lookup[node], new)
            if new != cluster_lookup[node] and move not in movements:
                movements.add(move)
                cluster_lookup[node] = new
                finished = False

    clusters = {}
    for k, v in cluster_lookup.iteritems():
        clusters.setdefault(v, []).append(k)

    # 类的内聚性指数
    inter_exponent = {}
    inter_weight = {}
    for cid, nodes in clusters.iteritems():
        nset = set(nodes)
        edges = [] # 内部元素相关度集合, 即cluster 内部边的权重
        for node in nodes:
            for target, weight in graph.edges.get(node, []):
                if weight:
                    edges.append(weight)
            nset.remove(node)
        inter_weight[cid] = edges

    # 将权重标准化
    i_w = {}
    for cid, inter_weight in inter_weight.iteritems():
        w = normalize(inter_weight)
        i_w[cid] = w
        inter_exponent[cid] = max(w) if w else 0.0

    return [(clusters[k], inter_exponent[k]) for k in clusters.keys()]

def get_distance_graph(documents):
    class Graph(object):
        def __init__(self):
            self.edges = {}

        def add_edge(self, n1, n2, w):
            self.edges.setdefault(n1, []).append((n2, w))
            self.edges.setdefault(n2, []).append((n1, w))
        def __str__(self):
            str_format = ""
            for key, value in self.edges.iteritems():
                str_format = "%s\n(%s: %s)" % (str_format, key, value)
            return str_format

    graph = Graph()
    doc_ids = range(len(documents))
    graph.nodes = set(doc_ids)
    # combinations 从 doc_ids 中生成所有可能的 2 元素排列组合, 不考虑前后顺序
    for a, b in combinations(doc_ids, 2):
        # a, b 均为 node 属于 nodes 集合
        graph.add_edge(a, b, cosine_distance(documents[a], documents[b]))
    return graph

def get_documents_old():
    texts = [
        "foo blub baz",
        "foo bar baz",
        "asdf bsdf csdf",
        "foo bab blub",
        "csdf hddf kjtz",
        "123 456 890",
        "321 890 456 foo",
        "123 890 uiop",
    ]
    return ([{"text": text, "tokens": text.split()}
             for i, text in enumerate(texts)],)

def get_documents_test():
    source = LinuxFansMysql()
    source.Connected()
    field_list = []
    doc_list = []
    for field, type_map in source.GetScheme():
        field_list.append(field)
    where = "pid in (111,222,333,444,555,666)"
    source.SetSql(field_list, where, offset=0, limit=100)
    while source.NextDocument():
        fields = {}
        for field in field_list:
            fields[field] = getattr(source, field)
        doc_list.append(fields)
    docs = []       # docs from select sql in database
    for doc in doc_list:
        docs.append((doc["pid"], doc["subject"], doc["message"]))
    return get_documents(docs)

def get_documents(docs):
    # docs only have the (docid, tokens, length of subject keyword)
    docs_tokens = []
    for doc in docs:
        tokens, sub_tok_len = get_keywords(doc[1], doc[2], tokenizer)
        docs_tokens.append((doc[0], tokens, sub_tok_len))

    for docid, tokens, sub_tok_len in docs_tokens:
        for i in range(sub_tok_len):
            # We change subject token weight to twice of its original
            tokens[i] = (tokens[i][0], tokens[i][1] * 2)
    # merge the same tokens
    def merge_tokens(tokens):
        tmp_tokens = {}
        for tok, count in tokens:
            if tmp_tokens.has_key(tok):
                tmp_tokens[tok] += count
            else:
                tmp_tokens[tok] = count
        return sorted(tmp_tokens.iteritems(), key=lambda d: d[1], reverse=True)
    docs_tokens_new = []
    for docid, tokens, sub_tok_len in docs_tokens:
        docs_tokens_new.append((docid, merge_tokens(tokens)))
    
    # appear frequence and appear documents of every token
    tokens_appear_map = {}
    doc_terms_count = {}
    for docid, tokens in docs_tokens_new:
        terms_count = 0
        for token, count in tokens:
            tokens_appear_map.setdefault(token,[]).append(docid)
            terms_count += count
        doc_terms_count[docid] = terms_count
    #for token, appear_list in tokens_appear_map.iteritems():
    #    print token, appear_list
    #for docid, tokens in docs_tokens_new:
    #    print docid, doc_terms_count[docid]

    # print the last result
    #for docid, tokens in docs_tokens_new:
    #    print docid
    #    for toks in tokens:
    #        print toks[0], toks[1]
    documents = []
    for docid, tokens in docs_tokens_new:
        token_map = {}
        for key, count in tokens:
            token_map[key] = {"count": count}
        token_list = [key[0] for key in tokens]
        documents.append({"text":   "id:%s\ntext:%s" % (docid, " ".join(token_list)),
                             "docid": docid,
                             "token_map": token_map,
                             "token_list": token_list})

    return documents, tokens_appear_map, doc_terms_count

def print_document_format(documents_format):
    global ret_str
    ret_str = ""
    def print_t(t):
        global ret_str
        ret_str = "%s%s\n" % (ret_str, t)
    documents, tokens_appear_map, doc_terms_count = documents_format
    for doc in documents:
        print_t("DocId: %s" % doc["docid"])
        print_t( "Text: %s" % doc["text"])
        print_t( "Document terms count: %s" % doc_terms_count[doc["docid"]])
        for token in doc["token_list"]:
            print_t("%s %s" % (token, doc["token_map"][token]))
            print_t("Appear doc list: %s" % tokens_appear_map[token])
    return ret_str

    
def main(args):
    documents_format = get_documents_test()
    get_cluster(documents_format)
if 0:
    NEW_FORMAT = True
    if NEW_FORMAT:
        documents_format = get_documents_test()
        documents, tokens_appear_map, doc_terms_count = documents_format
        #print_document_format(documents_format)
        add_tfidf_to(documents_format)
        dist_graph = get_distance_graph(documents)
    else:
        documents_format = get_documents_old()
        documents = documents_format[0]
        add_tfidf_to_old(documents)
        dist_graph = get_distance_graph(documents)

def get_cluster(documents_format):
    cluster_format = []
    documents, tokens_appear_map, doc_terms_count = documents_format
    add_tfidf_to(documents_format)
    dist_graph = get_distance_graph(documents)

    cluster_res = sorted(majorclust(dist_graph), key=lambda d: d[1], reverse=True)
    cid = 0
    for cluster, inter_weight in cluster_res:
        cid += 1
        #print "========="
        #print "Cluster %s Inter weight: %s" % (cid, inter_weight)
        keywords = {}
        docs_id = []
        for id in cluster:
            docs_id.append(documents[id]["docid"])
        for id in cluster:
            for token in documents[id]["token_list"]:
                intersection = set(tokens_appear_map[token]).intersection(set(docs_id))
                l = len(intersection)
                if l > 1:
                    keywords[token] = len(intersection)
        keywords_sorted = sorted(keywords.iteritems(), key=lambda d: d[1], reverse=True)
        #print "Keywords %s" % " ".join(["%s%s"%(key,v) for key, v in keywords_sorted])
        
        #for id in cluster:
            #print "ID: %s" % id, documents[id]["text"]
        cluster_format.append({"cid": cid, 
                               "inter_weight": inter_weight,
                               "docid_list": docs_id,
                               "keyword_list": keywords_sorted,
                               "keyword_map": keywords})
    return cluster_format

if __name__ == '__main__':
    main(sys.argv)
