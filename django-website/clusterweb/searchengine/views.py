# -*- coding=utf-8 -*-
# Create your views here.
from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.template import RequestContext
# from project.application.web_search....
from clusterweb.searchengine.web_search import google
import sphinxapi as sph
from LinuxFansSql import LinuxFansMysql
import sys
sys.path.insert(0, "/home/sunshine/Thesis/cluster")
import majorclust as clust
import copy
import types

host = 'localhost'
port = 9312
pagesize = 10
clust_docs_size = 100
keywordcount = 5
def sph_search(query, index="*", offset=0, limit=20):
    q = query
    index = index
    mode = sph.SPH_MATCH_ALL
    filtercol = 'group_id'
    filtervals = []
    sortby = ''
    groupby = ''
    groupsort = '@group desc'
    offset = offset
    limit = limit
    # Start sphinx
    cl = sph.SphinxClient()
    cl.SetServer ( host, port )
    #cl.SetFieldWeights({"subject": 500, "message": 100})
    cl.SetMatchMode ( mode )
    if filtervals:
        cl.SetFilter ( filtercol, filtervals )
    if groupby:
        cl.SetGroupBy ( groupby, sph.SPH_GROUPBY_ATTR, groupsort )
    if sortby:
        cl.SetSortMode ( sph.SPH_SORT_EXTENDED, sortby )
    if limit:
        cl.SetLimits ( offset, limit, max(limit,1000) )
    res = cl.Query ( q, index )

    # Format the result
    error = ""
    warning = ""
    ret_format = {}
    if not res:
        error = cl.GetLastError()
        return False, error

    if cl.GetLastWarning():
        warning = cl.GetLastWarning()

    ret_format["query"] = q
    ret_format["total"] = res['total']
    ret_format["total_found"] = res['total_found']
    ret_format["time"] = res['time']

    #print 'Query stats:'
    if res.has_key('words'):
        qstatus = {}
        #for info in res['words']:
        #print '\t\'%s\' found %d times in %d documents' % (info['word'], info['hits'], info['docs'])
        ret_format["words"] = res["words"]

    if res.has_key('matches'):
        matches = []
        n = offset + 1
        #print '\nMatches:'
        for match in res['matches']:
            #attrsdump = ''
            attrs_list = []
            match_each = {}
            for attr in res['attrs']:
                attr_map = {}
                attrname = attr[0]
                attrtype = attr[1]
                value = match['attrs'][attrname]
                if attrtype==sph.SPH_ATTR_TIMESTAMP:
                    value = time.strftime ( '%Y-%m-%d %H:%M:%S', time.localtime(value) )
                #attrsdump = '%s, %s=%s' % ( attrsdump, attrname, value )
                attr_map["name"] = attrname
                attr_map["value"] = value
                attrs_list.append(attr_map)

            #print '%d. docid=%s, weight=%d%s' % (n, match['id'], match['weight'], attrsdump)
            match_each["id"] = n
            match_each["docid"] = match["id"]
            match_each["weight"] = match["weight"]
            match_each["attrs"] = attrs_list
            matches.append(match_each)
            n += 1
        ret_format["matches"] = matches

    ret_format["error"] = error
    ret_format["warning"] = warning
    return True, ret_format

def sph_buildExcerpts(docs, index, words, opts=None):
    docs = docs
    words = words
    index = index
    if opts:
        opts = opts
    else:
        opts = {'before_match':'<em>', 'after_match':'</em>', 'chunk_separator':' ... ', 'limit':400, 'around':15}

    cl = sph.SphinxClient()
    cl.SetServer ( host, port )
    res = cl.BuildExcerpts(docs, index, words, opts)

    error=None
    if not res:
    	error = cl.GetLastError()
        return False, error
    else:
    	return True, [r.decode("utf-8") for r in res]

def pagination(total, pagesize, page_cur_start, padding=10):
    page_cur_num = page_cur_start/pagesize+1
    page_all_num = total/pagesize + (1 if total%pagesize!= 0 else 0)
    pages_num = []
    pages = []
    pad_l = page_cur_num-1
    pad_r = page_cur_num
    while pad_l > 0 and page_cur_num-pad_l < padding:
        pages_num.append(pad_l)
        pad_l=pad_l-1
    pages_num.reverse()
    while pad_r <= page_all_num and pad_r-page_cur_num < padding:
        pages_num.append(pad_r)
        pad_r=pad_r+1

    for page_num in pages_num:
        pages.append({"num": page_num, "start": (page_num-1)*pagesize})

    page_cur = {"num":page_cur_num, "start":page_cur_start}
    return page_cur, pages

def selectPosts(res, offset=None, limit=None):
    '''
        Select docs from Linuxfans database, where res parameter is:
        1. a string of pid. LIKE "1,2,3"
        2. a result format from sphinx result. usually a list type contain complex type.
        '''
    if type(res) == types.StringType:
        matches_id = res
    else:
        # Get matches id in res from sphinx result format
        matches_id = str([m["docid"] for m in res["matches"]])[1:-1]
    posts = []
    source = LinuxFansMysql()
    source.Connected()
    field_list = []
    for field, type_map in source.GetScheme():
        field_list.append(field)
    id_list = []
    where = "pid in (%s)" % matches_id
    
    source.SetSql(field_list, where, offset, limit)
    while source.NextDocument():
        post = {}
        for field in field_list:
            post[field] = getattr(source, field)
        posts.append(post)
    return posts

def get_cluster(query, keywordcount=None):
    status, res = sph_search(query, offset=0, limit = clust_docs_size)
    posts = selectPosts(res)
    docs = []
    for post in posts:
        docs.append((post["pid"], post["subject"], post["message"]))
    # There will Print all pid of the top 100 docs in clusters
    #print ",".join([str(p["pid"]) for p in posts])
    documents_format = clust.get_documents(docs)
    #f = open("/home/sunshine/clust.log","w")
    #f.write(clust.print_document_format(documents_format))
    #print clust.print_document_format(documents_format)
    #f.close()
    cluster_format = clust.get_cluster(documents_format)
    for cluster in cluster_format:
        cluster["keyword_list"] = cluster["keyword_list"][:keywordcount]
        cluster["keyword_list_str"] = " ".join([k[0] for k in cluster["keyword_list"]])
        cluster["docid_list_str"] = ",".join([str(id) for id in cluster["docid_list"]])
        cluster["docs_count"] = len(cluster["docid_list"])
    return cluster_format

def set_GET_para(request, context_content):
    # Auto Construct the GET parameter
    page_para = ""
    clust_para = ""
    get_para = copy.copy(request.GET)
    for key, para in get_para.iteritems():
        if key not in ("clust", "clust_key", "start"):
            page_para = "%s%s=%s&" % (page_para, key, para)
        if key not in ("clust", "clust_key", "start"):
            clust_para = "%s%s=%s&" % (clust_para, key, para)
    context_content["page_para"] = page_para[:-1]
    context_content["clust_para"] = clust_para[:-1]

def search(request):
    template = "search.html"
    context_content = {}
    query = request.GET.get('q','')
    start = int(request.GET.get('start','0'))

    set_GET_para(request, context_content)
    if query:
        status, res = sph_search(query, offset=start, limit = pagesize)
        page_cur, pages = pagination(res["total"], pagesize, start)
        context_content["pages"] = pages
        context_content["page_cur"] = page_cur

        if status:
            posts = selectPosts(res)
            for post in posts:
                st, (post["subject"], post["message"]) = \
                    sph_buildExcerpts([post["subject"], post["message"]],
                                      index="main", words=query)
            context_content["res"] = res
            context_content["posts"] = posts

            cluster_format = get_cluster(query, keywordcount)
            context_content["clusters"] = cluster_format
            context_content["cluster_count"] = len(cluster_format)

            return render_to_response(template, 
                                      context_content,
                                      context_instance = RequestContext(request))
        else:
            return render_to_response(template, {"error": res},
                                      context_instance = RequestContext(request))
        #(title, link,  description)
        #return render_to_response(res_template, res_content)
        #return HttpResponseRedirect("/")
    else:
        return render_to_response(template,
                                  #{"error": "Please Input Query String"},
                                  context_instance = RequestContext(request))
def sph_get_idrange(res, idrange, offset, limit):
    new_matchs_map = {}
    new_matchs_list = []
    idrange = [int(id) for id in idrange.split(',')]
    for match in res["matches"]:
        docid = match["docid"]
        if docid in idrange:
            new_matchs_map[docid] = match
    for id in idrange:
        new_matchs_list.append(new_matchs_map.get(id, []))
    res["matches"] = new_matchs_list
    return res
def get_sph_posts(request):
    context_content = {}
    template = "snippet/sph_post_tease.html"
    query = request.GET.get("q", "")
    start = int(request.GET.get("start", 0)) # format 20
    clust = str(request.GET.get("clust", ""))
    if query and clust:
        # do query from clust
        status, res = sph_search(query, offset=0, limit = clust_docs_size)
        if status:
            res = sph_get_idrange(res, clust, offset=start, limit = pagesize)
            context_content["res"] = res
            return render_to_response(template, 
                                      context_content,
                                      context_instance = RequestContext(request))
        else:
            return render_to_response(template, {"error": res},
                                      context_instance = RequestContext(request))
    elif query and not clust:
        # do query only
        status, res = sph_search(query, offset=start, limit = pagesize)
        if status:
            context_content["res"] = res
            return render_to_response(template, 
                                      context_content,
                                      context_instance = RequestContext(request))
        else:
            return render_to_response(template, {"error": res},
                                      context_instance = RequestContext(request))
    else:
        return render_to_response(template,
                                  context_instance = RequestContext(request))

def get_posts(request):
    # For GET only
    #if request.method == 'GET':
    context_content = {}
    template = "snippet/post_tease.html"
    query = request.GET.get("q", "")
    clust = str(request.GET.get("clust", "")) # format "1,2,3"
    clust_key = request.GET.get("clust_key", "")
    start = int(request.GET.get("start", 0)) # format 20
    set_GET_para(request, context_content)

    if query and clust:
        matches_id = clust
        page_cur, pages = pagination(len(clust.split(",")), pagesize, start)
        context_content["pages"] = pages
        context_content["page_cur"] = page_cur
        posts = selectPosts(matches_id, start, pagesize)
        for post in posts:
            st, (post["subject"], post["message"]) = \
                sph_buildExcerpts([post["subject"], post["message"]],
                                    index="main", words="%s %s" % (clust_key, query))
            #print "%s %s" % (clust_key, query)
        context_content["posts"] = posts
        return render_to_response(template, 
                                  context_content,
                                  context_instance = RequestContext(request))
    elif query and not clust:
        status, res = sph_search(query, offset=start, limit = pagesize)
        page_cur, pages = pagination(res["total"], pagesize, start)
        context_content["pages"] = pages
        context_content["page_cur"] = page_cur

        if status:
            posts = selectPosts(res)
            for post in posts:
                st, (post["subject"], post["message"]) = \
                    sph_buildExcerpts([post["subject"], post["message"]],
                                      index="main", words=query)
            context_content["posts"] = posts
        return render_to_response(template, 
                                  context_content,
                                  context_instance = RequestContext(request))
    else:
        return render_to_response(template,
                                  context_instance = RequestContext(request))

from django import template
template.add_to_builtins('searchengine.templatetags.search_tags')
