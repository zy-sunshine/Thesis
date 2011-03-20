#!/usr/bin/python
# -*- coding=utf-8 -*-
import sys
from math import log, sqrt
from itertools import combinations

def cosine_distance(a, b):
    cos = 0.0
    a_tfidf = a["tfidf"]
    for token, tfidf in b["tfidf"].iteritems():
        if token in a_tfidf:
            cos += tfidf * a_tfidf[token]
    return cos

def normalize(features):
    norm = 1.0 / sqrt(sum(i**2 for i in features.itervalues()))
    for k, v in features.iteritems():
        features[k] = v * norm
    return features

def add_tfidf_to(documents):
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

def choose_cluster(node, cluster_lookup, edges):
    new = cluster_lookup[node]
    if node in edges:
        seen, num_seen = {}, {}
        for target, weight in edges.get(node, []):
            # 与 target node 所属类的相似性(以到 target 类的 cosine 累加值来计算)
            seen[cluster_lookup[target]] = seen.get(
                cluster_lookup[target], 0.0) + weight
        for k, v in seen.iteritems():
            num_seen.setdefault(v, []).append(k)
        # 相似度越大越应被归为一类
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
        for node in graph.nodes:
            new = choose_cluster(node, cluster_lookup, graph.edges)
            move = (node, cluster_lookup[node], new)
            if new != cluster_lookup[node] and move not in movements:
                movements.add(move)
                cluster_lookup[node] = new
                finished = False

    clusters = {}
    for k, v in cluster_lookup.iteritems():
        clusters.setdefault(v, []).append(k)

    return clusters.values()

def get_distance_graph(documents):
    class Graph(object):
        def __init__(self):
            self.edges = {}

        def add_edge(self, n1, n2, w):
            self.edges.setdefault(n1, []).append((n2, w))
            self.edges.setdefault(n2, []).append((n1, w))

    graph = Graph()
    doc_ids = range(len(documents))
    graph.nodes = set(doc_ids)
    # combinations 从 doc_ids 中生成所有可能的 2 元素排列组合, 不考虑前后顺序
    for a, b in combinations(doc_ids, 2):
        # a, b 均为 node 属于 nodes 集合
        graph.add_edge(a, b, cosine_distance(documents[a], documents[b]))
    return graph

def get_documents():
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
    return [{"text": text, "tokens": text.split()}
             for i, text in enumerate(texts)]

def main(args):
    documents = get_documents()
    add_tfidf_to(documents)
    dist_graph = get_distance_graph(documents)

    for cluster in majorclust(dist_graph):
        print "========="
        for doc_id in cluster:
            print documents[doc_id]["text"]

if __name__ == '__main__':
    main(sys.argv)
