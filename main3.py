"""不打印日志版"""
import requests as r
import time
import config
import codecs,os,json,urllib,sys
from datetime import datetime as dt

def mergeDictListByKey(dictList1, dictList2, key):
    intListLengthBefore = len(dictList1)
    for elm2 in dictList2:
        existFlag = False
        for elm1 in dictList1:
            if elm2[key] == elm1[key]:
                existFlag = True
                break
        if not existFlag: dictList1.append(elm2)
    if intListLengthBefore != len(dictList1):
        print(f'〖本地列表合并变化{len(dictList1)-intListLengthBefore}〗 ({intListLengthBefore}->{len(dictList1)})')
    else:
        print(f'〖本地列表〗 ({intListLengthBefore})')
    return dictList1

class CloudMusic:
    def __init__(self,api,phone,phone_pwd,email,email_pwd,cookie):
        self.api = api
        self.phone=phone
        self.phone_pwd=phone_pwd
        self.email=email
        self.email_pwd=email_pwd
        self.cookie=cookie
        self.s=r.session()

    def get(self,url):
        return self.s.get( self.api + url + ( f"{'&' if '?' in url else '?'}cookie={urllib.parse.quote_plus(self.cookie)}" if self.cookie else "" ) )
    
    def login(self,cookie_refresh):
        """登录"""
        uid,login_data = ( None, None )
        if self.cookie: uid,login_data = self.loginStatus()
        if not uid or cookie_refresh == '1':
            # 邮箱登录
            print(f'尝试邮箱登录')
            res = self.get('/login?email=%s&password=%s' % (self.email, self.email_pwd))
            data = res.json()
            if data.get('account'):
                uid,login_data = ( data.get('account').get('id'), data )
                print(f'邮箱登录成功')
            else:
                print(f'邮箱登录失败:{str(data)}')
                # 手机号登录
                print(f'尝试手机号登录')
                res = self.get('/login/cellphone?phone=%s&password=%s' % (self.phone, self.phone_pwd))
                data = res.json()
                if data.get('account'):
                    uid,login_data = ( data.get('account').get('id'), data )
                    print(f'手机号登录成功')
                else:
                    print(f'手机号登录失败:{str(data)}')
            # 二维码登录参考  https://github.com/crayonxin2000/NeteaseCloudPlayListDownload/blob/be6806a325a3e8c1b4626bb02e25d19a165a3334/musics.py https://github.com/NKID00/NeteaseCloudMusicApiPy/blob/731e8c405928d38be693739cff6449e3426d22c7/ncmapi.py
            # key = self.get('/login/qr/key?timerstamp=%s' % (time.time())).json().get('data').get('unikey')
            # qrimg = self.get('/login/qr/create?key=%s&qrimg=true&timerstamp=%s' % (key, time.time())).json().get('data').get('qrimg')
            # self.get('/login/qr/check?key=%s&timerstamp=%s' % (key, time.time())).json()
            # data = self.get('/login/qr/check?key=%s&timerstamp=%s' % (key, time.time())).json()
            # if data.get('code')== 803: print(f'授权登录成功,返回cookie[{data.get('cookie')}])
            # 邮箱登录参考
            if data.get('cookie') and str(data.get('cookie')).strip():
                try:
                    ( date_str_old, date_str_new ) = ( self.cookie.partition("MUSIC_U=")[2].partition("Expires=")[2].partition(";")[0], data.get('cookie').partition("MUSIC_U=")[2].partition("Expires=")[2].partition(";")[0] )
                    ( date_old, date_new ) = ( dt.strptime(date_str_old, "%a, %d %b %Y %H:%M:%S %Z"), dt.strptime(date_str_new, "%a, %d %b %Y %H:%M:%S %Z") )
                    if date_old<date_new:
                        print(f'cookie应该更新[{date_str_old} -> {date_str_new}]')
                        self.cookie=data.get('cookie')
                        print(f"OUTVAR_COOKIE:{data.get('cookie')}")
                    else:
                        print(f'cookie无需更新[{date_str_old} -> {date_str_new}]')
                except ValueError:
                    print(f'cookie更新异常[{date_str_old} -> {date_str_new}]')
        return ( uid,login_data )

    def loginStatus(self):
        """获取登录状态"""
        print(f'尝试cookie登录')
        res=self.get('/login/status?timerstamp=%s' % (time.time()))
        data=res.json()
        if data and data.get('data') and data.get('data').get('code')==200 and data.get('data').get('account') and data.get('data').get('account').get('status')==0:
            print(f'cookie登录成功')
            return ( data.get('data').get('account').get('id'), data )
        else:
            print(f'cookie登录失败:{str(data)}')
        return ( None, data )

    def refresh(self):
        """刷新登录状态"""
        res=self.get('/login/refresh')
        data=res.json()
        if data.get('code')==200:
            return True
        print(data)
        return False

    def createMusicList(self,name):
        """创建歌单"""
        res=self.get('/playlist/create?name=%s'%name)
        data=res.json()
        id=data.get('id')
        return id

    def getDaySend(self):
        """获取每日推荐"""
        res=self.get('/recommend/songs')
        data=res.json()
        recommend=data.get('recommend')
        ids=[]
        for item in recommend:
            ids.append(str(item.get('id')))
        return ids[::-1]

    def addMusicToList(self,list_id,music_ids):
        """添加歌单歌曲"""
        res=self.get('/playlist/tracks?op=add&pid=%s&tracks=%s'%(list_id,music_ids))
        #print('/playlist/tracks?op=add&pid=%s&tracks=%s'%(list_id,music_ids))
        data=res.json().get('body') if res.json().get('body') else res.json()
        if data and data.get('code')==200:
            return ""
        return f"{data.get('code')}-{data.get('message')}" if data and data.get('code') else f"unrecognized res:{res.json()}"

    def getMusicListDetail(self,list_id):
        """获取歌单详情"""
        res=self.get('/playlist/detail?id=%s'%list_id)
        data=res.json()
        playlist=data.get('playlist')
        if not playlist:
            return []
        tracks=playlist.get('tracks')
        ids=[]
        for item in tracks:
            ids.append(str(item.get('id')))
        return ids

    def getMusicListTracks(self,list_id,save_with_name=""):
        """获取歌单所有歌曲"""
        res=self.get(f'/playlist/track/all?id={list_id}&limit=827')
        data=res.json()
        tracks=data.get('songs')
        if save_with_name and tracks:
            #print(f'〖歌单保存({save_with_name})〗')
            #data = dict({"name":save_with_name, "count":len(tracks)}).update(data)
            data = {"名称":save_with_name, "总数":len(tracks),**data} # 增加 歌单名称 和 歌曲总数 数据项
            if not os.path.exists(os.path.dirname(os.path.abspath(__file__))+'/playlist_backup'): os.makedirs(os.path.dirname(os.path.abspath(__file__))+'/playlist_backup')
            f = codecs.open(os.path.dirname(os.path.abspath(__file__))+'/playlist_backup/playlist('+save_with_name+').json', 'a+', encoding='utf-8')
            if f.tell():  # 文件已存在数据,则将返回的歌曲并入其中
                f.seek(0)
                data["songs"] = mergeDictListByKey(json.load(f)["songs"], tracks, "id") # 根据ID合并更新歌曲数据
                data["总数"] = len(data["songs"]) # 更新 歌曲总数
            f.seek(0)
            f.truncate()
            json.dump(data, f, sort_keys=False, indent=None, ensure_ascii=False)
        ids=[]
        if tracks:
            for item in tracks:
                ids.append(str(item.get('id')))
        return ids

    def getUserMusicList(self,uid):
        """获取用户歌单"""
        res=self.get('/user/playlist?uid=%s'%uid)
        data=res.json()
        playlist=data.get('playlist')
        if not playlist:
            return []
        detail={}
        for item in playlist:
            id=item.get('id')
            name=item.get('name')
            if id and name:
                detail[name]=str(id)
        return detail

    def qiandao(self):
        """签到"""
        res = self.get('/daily_signin')
        data = res.json()
        print(data)



if __name__=='__main__':
    api=config.api
    phone=config.phone
    phone_pwd=config.phone_pwd
    email=config.email
    email_pwd=config.email_pwd
    argvLength = len(sys.argv)
    cookie = sys.argv[1] if argvLength>1 else ""  # 参数1-Cookie
    cookie_refresh = sys.argv[2] if argvLength>2 else ""  # 参数2-Cookie刷新(值为字符串"1"时强制刷新)
    print('开始登录')
    cm=CloudMusic(api,phone,phone_pwd,email,email_pwd,cookie)
    uid,login_data=cm.login(cookie_refresh)
    if not uid:
        print(f'账号登录失败:{str(login_data)}')
        exit(0)
    print(f'【uid={str(uid)}】【login_data={str(login_data)}】')
    try:
        if uid:  # 登录成功时签到
            print('开始签到')
            cm.qiandao()
        print('开始处理歌单')
        #if int(time.strftime('%H'))<8:
            #网易云6点更新推荐 8点后处理避免将昨天的歌单放到今天的歌单里
        #    print('不到8点，不处理')
        #    exit(0)
        user_music_list = cm.getUserMusicList(uid)
        SYNC_LIST = {'宝藏系女孩@5160012695':'Exotic', 
                  '[聚精会神]@2829821753':'Concentration',
                  '闽南语精选@6686195798':'Minnan',
                  '[闽南语唱片行]@7525397914':'Minnan',
                  '[东方禅意]@6867586378':'Chinese Folk',
                  '[宝藏系男孩]@5092779494':'Exotic Male', 
                  '[怀旧点唱机]@5199155506':'80s',  
                  '[时光点唱机]@2945028696':'90s', 
                  '[青春点唱机]@2968527373':'00s',  
                  '[流行点唱机]@5172410111':'10s', 
                  '80年代精选@6686195201':'80s collection',
                  '90年代精选@6686195202':'90s collection',
                  '00年代精选@6685670200':'00s collection',  
                  '10年代精选@6686195200':'10s collection', 
                  '缠绵精选@6686195204':'Romantic', 
                  '休憩专享@6686195312':'Downtempo', 
                  '[牛奶泡泡浴]@2638104052':'Lazy', 
                  '[浴室歌王]@7706521452':'Showerbath', 
                  '[爱的巴萨诺瓦]@5296889333':'Bossa Nova', 
                  '[今夜晚点睡]@5160019130':'Romance', 
                  '[浪漫婚礼专用]@898150':'Sweet Love', 
                  '[阅读好时光]@2768646174':'Reading', 
                  '[运动随身听]@2829779628':'Sports',  
                  '[大自然纯音]@2919023249':'Nature', 
                  '[古典歌剧典藏]@5453498110':'Opera', 
                  '[开启学霸模式]@2821046530':'Western Classical', 
                  '[放刺一周电音]@2946898175':'Electronic', 
                  '[电音小情歌]@6916067530':'Electronic Love', 
                  '[公路之歌]@5089862808':'Roadtrip', 
                  '[放克复古派对]@6654541946':'Funk', 
                  '华语私人@2829883282':'Chinese',
                  '[粤语唱片行]@3455816':'Cantonese',
                  '听·王菲@7720523469':'Faye',
                  '[法语浪漫订制]@5180278369':'French', 
                  '西语精选#西班牙语精选@6686195801':'Spanish',
                  '德语精选@6686195795':'German', 
                  '越南语精选@6686195803':'Vietnamese', 
                  '泰语精选@6686195800':'Thai', 
                  '韩语精选#K-pop@6686195797':'Korean', 
                  '[韩系小甜歌]@6651601935':'Korean Sweet', 
                  '日本流行精选@6686195387':'Japanese', 
                  '有声书精选@6686195452':'Audible', 
                  '[儿童趣味百科]@6630204532':'Children Wiki', 
                  '[亲子玩耍时光]@5061008960':'Children Joy', 
                  '[宝贝安全教育]@5466062741':'Children Safety', 
                  '[亲子早教儿歌]@6633211694':'Children Early Education', 
                  '[儿童诗词吟唱]@2639193881':'Children Poems', 
                  '[亲子欢乐儿歌]@5331303031':'Children Games'}
         # 虚位以待 深厚磁性男声
        for src_list_keywords,dst_list_name in SYNC_LIST.items():
            src_list_id = src_list_keywords.partition("@")[2]
            if src_list_id and src_list_id in user_music_list.values():  # 优先从名字中获取歌单ID
                print('【源歌单已找到】%s' % str((src_list_id,list(user_music_list.keys())[list(user_music_list.values()).index(src_list_id)])) )
            elif uid:   # 其次获取歌单列表并通过关键字匹配
                for list_name in user_music_list:
                    for src_list_keyword in src_list_keywords.partition("@")[0].strip("# ").split("#"):
                        if src_list_keyword in list_name:
                            src_list_id = user_music_list[list_name]
                            print('【源歌单已找到】%s' % str((src_list_id,list_name)) )
                            break
                    if src_list_id: break
            if not src_list_id:
                print('【源歌单未找到】%s' % str((src_list_keywords,user_music_list)) )
                continue
            #src_list_music_ids = cm.getMusicListDetail(src_list_id)
            src_list_music_ids = cm.getMusicListTracks(src_list_id,dst_list_name)
            print(f'〖源歌单列表({str(len(src_list_music_ids))})〗') #：{str(src_list_music_ids)}
            dst_list_id = dst_list_name.partition("@")[2]
            if dst_list_id:  # 优先从名字中获取歌单ID
                print('〖目标歌单已存在〗%s' % str((dst_list_id)) )
            elif dst_list_name in user_music_list:   # 其次获取歌单列表并通过关键字匹配
                dst_list_id = user_music_list[dst_list_name]
                #dst_list_music_ids = cm.getMusicListDetail(dst_list_id)
                dst_list_music_ids = cm.getMusicListTracks(dst_list_id,dst_list_name)
                print('〖目标歌单已存在〗%s' % str((dst_list_id,dst_list_name,len(dst_list_music_ids))))
            else:
                (dst_list_id,dst_list_music_ids) = (cm.createMusicList(dst_list_name),[])
                print('〖目标歌单已新建〗%s' % str((dst_list_id,dst_list_name,0)))
            #day_music_ids = cm.getDaySend()
            will_add_list = []
            for music_id in src_list_music_ids:
                if music_id in dst_list_music_ids:
                    pass
                else:
                    will_add_list.append(music_id)
            if len(will_add_list) > 0:
                music_ids = ','.join(will_add_list)
                errmsg = cm.addMusicToList(dst_list_id, music_ids)
                if not errmsg:
                    print(f'━━▶添加歌曲列表成功【+{str(len(will_add_list))}】：{music_ids}')
                else:
                    print(f'◀━━添加歌曲列表失败【{str(len(will_add_list))}】：[{str(errmsg)}]{music_ids}')
    except Exception as e:
        import traceback
        errmsg = '(E)' + '[' + ''.join(traceback.format_exc()) + ']'
        print(errmsg)

"""测试语句
/usr/bin/python3.6
import requests as r
s=r.session()
(PhoneNo,Passwd) = ("","")
s.get(f"http://127.0.0.1:3000/login/cellphone?phone={PhoneNo}&password={Passwd}").json()
s.get("http://127.0.0.1:3000/daily_signin").json()
data=s.get("http://127.0.0.1:3000/user/playlist?uid=116945513").json()
data=s.get("http://127.0.0.1:3000/playlist/detail?id=5160012695").json()
playlist=data.get('playlist')
tracks=playlist.get('tracks')
ids=[]
for item in tracks:
    ids.append(str(item.get('id')))
print(ids)
data=s.get("http://127.0.0.1:3000/playlist/track/all?id=5160012695&limit=827").json()
tracks=data.get('songs')
ids=[]
for item in tracks:
    ids.append(str(item.get('id')))
print(ids)
data=s.get("http://127.0.0.1:3000/recommend/songs").json()
recommend=data.get('data').get('dailySongs')
ids=[]
for item in recommend:
    ids.append(str(item.get('id')))
data=s.get("http://127.0.0.1:3000/playlist/tracks?op=add&pid=7124292374&tracks=26771764").json().get('body')
f"{data.get('code')}-{data.get('message')}"
"""

