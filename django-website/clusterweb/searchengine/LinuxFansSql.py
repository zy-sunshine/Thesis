#!/usr/bin/env python
# -*- coding:utf-8 -*-
import MySQLdb,logging
import dict4ini
import sys
sys.path.insert(0, "/usr/local/coreseek/etc/pysource/csft_demo_pymysql")
import tstruct
from tstruct import post_field, confFilePrivate
import logging
import types

def loadConfig(inifile):
    return dict4ini.DictIni(inifile)
    
def setLoggerHandler(logfile):
    logging.basicConfig(filename=logfile,level=logging.DEBUG)
    
def log_info(info):
    logging.debug(info)
    
def log_erro(info):
    logging.debug(info)

class LinuxFansMysql(object):
    def __init__(self):
        self.cfg=loadConfig(confFilePrivate)
        setLoggerHandler(self.cfg.logging.logfile)
        self.m_dbconn = None
        self._rowCount=0
        self.m_curid = None
        #base str
        self.field = {}
        self.m_basesql_str = ''
        for item in post_field:
            fname, ftype = item[tstruct.fname], item[tstruct.ftype]
            if ftype == "docid":
                self.field["docid"] = fname
            exec('self.%s = None' % fname)
        self.m_finished = None
        
    def GetScheme(self):
        #获取结构，docid、文本、整数
        ret = []
        for item in post_field:
            fname, ftype = item[tstruct.fname], item[tstruct.ftype]
            if ftype == "text":
                ret.append((fname, {"type": "text"}))
            elif ftype == "integer":
                ret.append((fname, {"type": "integer"}))
            elif ftype == "docid":
                ret.append((fname, {"docid": True}))
        return ret

    def Connected(self):
        if not self.cfg.has_key('mysql'):
            log_erro('Not has MySQL info')
            return False
        try:
            self.m_dbconn =  MySQLdb.connect (host = self.cfg.mysql.host,\
                port = int(self.cfg.mysql.port),\
                user = self.cfg.mysql.username,\
                passwd = self.cfg.mysql.password,\
                db = self.cfg.mysql.dbname)
        except MySQLdb.Error, e:
            logging.error( "Error %d: %s" , e.args[0], e.args[1])
            return False
        return True

    def SetSql(self, field_list, where, offset=None, limit=None):
        sql = """SELECT"""
        for fname in field_list:
            sql = """%s a.%s AS %s,""" % (sql, fname, fname)
        sql = """%s FROM %s%s AS a""" % (sql[:-1], self.cfg.mysql.tableprefix, self.cfg.mysql.table0)
        sql = """%s WHERE %s""" % (sql, "%(where)s")
        if offset is not None and limit is not None:
            sql = """%s limit %s, %s""" % (sql, offset, limit)
        self.m_basesql_str = sql
        self.m_finished = False
        if type(where) == types.ListType:
            self.m_where = where
        else:
            self.m_where = [where]
        return True
        
    def NextDocument(self):
	    ret = self._getAvailableRow()
	    return ret
	    
    def _getAvailableRow(self):
        if self._rowCount <= 0:
            #do fetch
            try:
                self.m_cursor = self.m_dbconn.cursor(cursorclass=MySQLdb.cursors.DictCursor)
                if self.m_where:
                    condition = self.m_where.pop(0)
                else:
                    # Select Terminate
                    return False

                self._rowCount = self.m_cursor.execute(self.m_basesql_str %
                        {"where": condition})
                return self._getRow()
                
            except MySQLdb.Error, e:
                log_erro( "Error %d:%s" % (e.args[0],e.args[1]))
                return False
        else:
            return self._getRow()

    def _getRow(self):
        m_row=self.m_cursor.fetchone()
        self._rowCount-=1
        if m_row:
            for item in post_field:
                fname, ftype = item[tstruct.fname], item[tstruct.ftype]
                if ftype in ("docid", "integer"):
                    if m_row[fname]:
                        exec('self.%s = m_row[fname]' % fname)
                    else:
                        exec("self.%s = 0" % fname)
                elif ftype in ("text",):
                    if m_row[fname]:
                        exec("self.%s = m_row[fname].decode(self.cfg.mysql.charset,'ignore').encode('utf8')" % fname)
                    else:
                        exec("self.%s = ''" % fname)
            log_info(str(m_row[self.field["docid"]]))
            self.m_curid = m_row[self.field["docid"]]
            return True
        else:
            return False
            
    def Finished(self):
        return True

            
if __name__ == "__main__":
    source = LinuxFansMysql()
    source.Connected()

    field_list = []
    for field, type_map in source.GetScheme():
        field_list.append(field)
    where = "pid in (1,2)"
    source.SetSql(field_list, where, offset=0, limit=100)
    while source.NextDocument():
        for field in field_list:
            print getattr(source, field),
        print 
if 0:
    conf = {}
    source = MainSource(conf)
    source.Connected()
    source.OnBeforeIndex()
    print source.m_maxid
    print source.m_minid
    (pid, subject, message) = (None, None, None)
    next_status = source.NextDocument()
    d_count = 0
    while next_status:#not source.m_finished
        #print "id=%d, subject=%s ,content =%s" % (source.pid, source.subject,source.message[0:20])
        (pid, subject) = (source.pid, source.subject)
        if source.message:
            message = source.message[0:20]
        if next_status:
            d_count+=1
        next_status = source.NextDocument()
    print d_count
    print (pid, subject, message)

