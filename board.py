import time
import datetime
import socket
import threading
import pymysql
import urllib.parse
import base64
import re
import math
import html

#mysqlへのconnectionを返す
def mysql_connect():
    CONTENTS = pymysql.connect(
        host='localhost',
        user='root',
        password='19431943',
        database='enshu',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor)
    return CONTENTS

#mysqlのmainテーブルを製作
def init_my_server():
    CONTENTS=mysql_connect()
    CURSOR = CONTENTS.cursor()
    CURSOR.execute("""CREATE TABLE IF NOT EXISTS main (
        id int NOT NULL AUTO_INCREMENT,
        title varchar(255) UNIQUE NOT NULL,
        time varchar(128) NOT NULL,
        PRIMARY KEY (id)
    )""")
    CONTENTS.commit()
    CURSOR.close()
    CONTENTS.close()

#投稿用フォームのテンプレを用意
MASTER_FILE_POINT = open('post.html', 'r')
MASTER_POST_FORM= (''.join(MASTER_FILE_POINT.readlines()))
MASTER_FILE_POINT.close()
#スレッド製作フォームのテンプレを用意
MASTER_FILE_POINT = open('put.html', 'r')
MASTER_PUT_FORM= (''.join(MASTER_FILE_POINT.readlines()))
MASTER_FILE_POINT.close()
#faviconを用意
FAVICON_POINT = open("favicon.ico", 'br')
FAVICON="data:image/vnd.microsoft.icon;base64,"
FAVICON += (base64.b64encode(FAVICON_POINT.read())).decode("utf-8")
FAVICON_POINT.close()
#cssを用意
CSS_POINT = open("page.css", 'r')
CSS = (''.join(CSS_POINT.readlines()))
CSS_POINT.close()

#送信するhtmlの文字列を作成
def page_maker(status,header,path,page,alert):
    CONTENTS = mysql_connect()
    CURSOR = CONTENTS.cursor()
    step=10
    if((int)(page)>0):
        offset=10*page
    else:
        offset=0
    css='<style type="text/css"><!--'
    if(status.startswith("4")):
        TITLE=status
        css=""
    elif(path==""):
        TITLE="掲示板"
    else:
        CURSOR.execute('SELECT * FROM main WHERE id=%s', (path))
        result=CURSOR.fetchone()
        TITLE=(str)(result["title"])
    TITLE=html.escape(TITLE,True)
    sent_message="HTTP/1.0 " + status + "\r\n"
    sent_message+=header + "\r\n"
    sent_message+="\r\n"
    sent_message+='<html lang="ja"><head><meta charset="UTF-8"><title>'+TITLE+'</title><link rel="icon" type="image/x-icon" href="'+FAVICON+'">'
    sent_message+='<style type="text/css"><!--'
    sent_message+=CSS
    sent_message+="--></style></head>"
    sent_message+='<a href="/"><h1>'+TITLE+'</h1></a>'
    if(alert!=""):
        sent_message+='<div class="box24"><font size="5">'+ alert + '</font><br></div>\n'
    if(status.startswith("4")):
        sent_message+=status
    elif(path==""):
        CURSOR.execute('select * from main order by time desc')
        try:
            max_id = CURSOR.fetchone()["id"]
        except:
            max_id=1
        sent_message+="<h2>スレッド一覧</h2>"
        sent_message+='<a href="/">Topへ</a>  '
        for i in range(math.ceil(max_id/step)):
            sent_message+='<a href="/?page='+(str)(i)+'">'+(str)(i+1)+'</a> '
        sent_message+='<hr>'
        CURSOR.execute('select * from main order by id desc limit '+(str)(step)+' offset '+(str)(offset))
        result = CURSOR.fetchall()
        if(len(result)>0):
            for l in result:
                value=html.escape((str)(l["title"]),True)
                value=('<br>'.join((str)(urllib.parse.unquote(value)).splitlines()))
                sent_message+='<div class="box22">'+(str)(l["id"])+' : <a href="' + (str)(l["id"]) + '">'+value+'</a>　(<I>"'+l["time"]+'"</I>)<br></div>\n'
        else:
            sent_message+="表示するスレッドがありません"
        sent_message+='<hr>'
        sent_message+='<a href="/">Topへ</a>  '
        for i in range(math.ceil(max_id/step)):
            sent_message+='<a href="/?page='+(str)(i)+'">'+(str)(i+1)+'</a> '
        sent_message+=MASTER_PUT_FORM
        sent_message+="<hr>"
    else:
        sent_message+="<h2>投稿一覧</h2>"
        if(path!="favicon.ico" and path!="page.css"):
            CURSOR.execute('select * from lines'+path+' order by id desc')
            try:
                max_id = CURSOR.fetchone()["id"]
            except:
                max_id=1
            sent_message+='<a href="/">Topへ</a>  '
            for i in range(math.ceil(max_id/step)):
                sent_message+='<a href="/'+path+'?page='+(str)(i)+'">'+(str)(i+1)+'</a> '
            sent_message+='<hr>'
            CURSOR.execute('select * from lines'+path+' order by dest,id limit '+(str)(step)+' offset '+(str)(offset))
            result = CURSOR.fetchall()
            if(len(result)>0):
                for l in result:
                    value=html.escape((str)(l["value"]),True)
                    value=re.sub(r'(&gt;&gt;)([0-9]+)',r'<a href=#\2>\1\2</a>', value)
                    value=re.sub(r'(https?://[\w/:%#&?()~.=+-]+)',r'<a href=\1>\1</a>', value,flags=re.MULTILINE)
                    value=('<br>'.join((str)(urllib.parse.unquote(value)).splitlines()))
                    if(l["id"]==l["dest"]):
                        sent_message+='<div class="box22" id="'+(str)(l["id"])+'">'+(str)(l["id"])+" : <b>" + l["name"] + "</b>　(<I>"+l["time"]+"</I>)<br><font color=" + l["fcolor"] + " size=" + l["fsize"] +">" + value + "</font><br></div>\n"
                    else:
                        sent_message+='<div class="box23" id="'+(str)(l["id"])+'">'+(str)(l["id"])+" : <b>" + l["name"] + "</b>　(<I>"+l["time"]+"</I>)<br><font color=" + l["fcolor"] + " size=" + l["fsize"] +">" + value + "</font><br></div>\n"
            else:
                sent_message+="表示する投稿がありません"
            sent_message+='<hr>'
            sent_message+='<a href="/">Topへ</a>  '
            for i in range(math.ceil(max_id/step)):
                sent_message+='<a href="/'+path+'?page='+(str)(i)+'">'+(str)(i+1)+'</a> '
            if(max_id<1001):
                sent_message+=MASTER_POST_FORM
            else:
                sent_message+="これ以上の投稿はできません"
            sent_message+="<hr>"
    CURSOR.close()
    CONTENTS.close()
    return sent_message

#cssを送信する
def css_maker():
    status="200 OK"
    header = "content-type: text/css"
    sent_message="HTTP/1.0 " + status + "\r\n"
    sent_message+=header + "\r\n"
    sent_message+="\r\n"
    sent_message+=CSS
    return sent_message


def worker_thread(serversocket):
    """クライアントとの接続を処理するハンドラ"""
    while True:
        # クライアントからの接続を待ち受ける (接続されるまでブロックする)
        # ワーカスレッド同士でクライアントからの接続を奪い合う
        clientsocket, (client_address, client_port) = serversocket.accept()
        print('New client: {0}:{1}'.format(client_address, client_port))

        while True:
            message=""
            alert=""
            try:
                message += (clientsocket.recv(4096)).decode("utf-8")
                print('Recv: {0} from {1}:{2}'.format(message,client_address,client_port))
            except OSError:
                break

            if len(message) == 0:
                break

            #GETの場合
            if(message.startswith("GET")):
                CONTENTS=mysql_connect()
                cursor=CONTENTS.cursor()
                tmp=message.splitlines()
                param=(str)(tmp[0].split()[1]).split("?")
                path=param[0].lstrip("/")
                page=0
                if(len(param)>1):
                    param=param[1].split("&")
                    for i in param:
                        if(i.startswith("page=")):
                            page=(int)(i.split("=")[1])
                sql="SELECT 1 FROM lines"+path+" LIMIT 1;"
                header = "Content-Type: text/html; charset=utf-8"
                print(path)
                if(path=="page.css"):
                    sent_message=css_maker()
                else:
                    if(path=="favicon.ico"):
                        break
                    elif(path==""):
                        status = "200 OK"
                    else:
                        try:
                            cursor.execute(sql)
                        except:
                            status ="404 Not Found"
                        else:
                            status = "200 OK"
                    sent_message=page_maker(status,header,path,page,alert)
                sent_message=sent_message.encode("utf-8")
                while True:
                    sent_len = clientsocket.send(sent_message)
                    if sent_len == len(sent_message):
                        break
                    sent_message = sent_message[sent_len:]

            #送信方法がPOSTの場合
            elif(message.startswith("POST")):
                CONTENTS=mysql_connect()
                cursor=CONTENTS.cursor()
                tmp=message.splitlines()
                param=(str)(tmp[0].split()[1]).split("?")
                url=param[0].lstrip("/")
                page=0
                if(len(param)>1):
                    param=param[1].split("&")
                    for i in param:
                        if(i.startswith("page=")):
                            page=(int)(i.split("=")[1])
                params=tmp[-1].split("&")
                dic={}
                for c in params:
                    tmp=c.split("=")
                    dic[tmp[0]]=('\r\n'.join((str)(urllib.parse.unquote(tmp[1])).splitlines()))
                #POSTの場合
                if(dic["_method"]=="POST"):
                    status="201 Created"
                    if(url!=""):
                        sql="INSERT INTO lines"+url+" VALUES (%s,%s,%s,%s,%s, %s,%s)"
                        ts = time.time()
                        timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                        try:
                            cursor.execute(sql, (0,dic["name"], timestamp,dic["value"],dic["fcolor"],dic["fsize"],1))
                        except:
                            alert="投稿失敗"
                        else:
                            alert="投稿完了"
                        cursor.execute('select * from lines'+url+' order by id desc')
                        max_id=cursor.fetchone()["id"]
                        sql='UPDATE lines'+url+' SET dest=%s WHERE time=%s'
                        if(dic["dest"]!=""):
                            if((int)(dic["dest"])>0 and (int)(dic["dest"])<max_id):
                                cursor.execute('select * from lines'+url+' where id=%s',((int)(dic["dest"])))
                                tmp=cursor.fetchone()
                                if(tmp["id"]==tmp["dest"]):
                                    cursor.execute(sql,((int)(dic["dest"]),timestamp))
                                else:
                                    cursor.execute(sql,((int)(tmp["dest"]),timestamp))
                            else:
                                cursor.execute(sql,(max_id,timestamp))
                        else:
                            cursor.execute(sql,(max_id,timestamp))
                        try:
                            CONTENTS.commit()
                        except:
                            alert="データベースで衝突が起こりました"
                            status="409 Conflict"
                #PUTの場合
                elif(dic["_method"]=="PUT"):
                    status="201 Created"
                    if(dic["name"]!=""):
                        ts = time.time()
                        timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                        sql="INSERT main VALUES (%s,%s,%s)"
                        try:
                            cursor.execute(sql, (0,dic["name"], timestamp))
                        except pymysql.err.IntegrityError:
                            alert="既に存在するスレッドです"
                        finally:
                            cursor.execute('SELECT * FROM main WHERE title=%s', (dic["name"]))
                            result=cursor.fetchone()
                            if(alert!="既に存在するスレッドです"):
                                sql="CREATE TABLE IF NOT EXISTS lines"+(str)(result["id"])+" ("
                                sql+="id smallint unsigned NOT NULL AUTO_INCREMENT,"
                                sql+="name varchar(32) NOT NULL,"
                                sql+="time varchar(128) NOT NULL,"
                                sql+="value varchar(8192) NOT NULL,"
                                sql+="fcolor varchar(12) NOT NULL,"
                                sql+="fsize varchar(4) NOT NULL,"
                                sql+="dest smallint unsigned NOT NULL,"
                                sql+="PRIMARY KEY (id))"
                                cursor.execute(sql)
                                try:
                                    CONTENTS.commit()
                                except:
                                    status="409 Conflict"
                                    alert="データベース内で衝突が起こりました"
                                else:
                                    alert="スレッド作成完了"
                    else:
                        status="400 Bad Request"

                header = "Content-Type: text/html; charset=utf-8"
                sent_message=page_maker(status,header,url,page,alert).encode("utf-8")

                #送信
                while True:
                    sent_len = clientsocket.send(sent_message)
                    if sent_len == len(sent_message):
                        break
                    sent_message = sent_message[sent_len:]

                cursor.close()
                CONTENTS.close()

            clientsocket.close()
            print('Bye-Bye: {0}:{1}'.format(client_address, client_port))


def main():
    init_my_server()
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

    host = 'localhost'
    port = 17079
    serversocket.bind((host, port))

    serversocket.listen(128)

    # サーバソケットを渡してワーカースレッドを起動する
    NUMBER_OF_THREADS = 20
    for _ in range(NUMBER_OF_THREADS):
        thread = threading.Thread(target=worker_thread, args=(serversocket, ))
        thread.daemon = True
        thread.start()

    while True:
        # メインスレッドは遊ばせておく (ハンドラを処理させても構わない)
        time.sleep(1)


if __name__ == '__main__':
    main()