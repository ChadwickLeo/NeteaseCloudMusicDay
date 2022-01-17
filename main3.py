"""不打印日志版"""
import requests as r
import time
import config
import codecs,os,json

class CloudMusic:
    def __init__(self,api,phone,password):
        self.api = api
        self.phone=phone
        self.password=password
        self.s=r.session()

    def get(self,url):
        return self.s.get(self.api+url)

    def login(self):
        """登录"""
        res = self.get('/login/cellphone?phone=%s&password=%s' % (self.phone, self.password))
        data=res.json()
        if data.get('account'):
            return data.get('account').get('id')
        return None

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
        data=res.json().get('body')
        if data.get('code')==200:
            return ""
        return f"{data.get('code')}-{data.get('message')}"

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

    def getMusicListTracks(self,list_id):
        """获取歌单所有歌曲"""
        res=self.get(f'/playlist/track/all?id={list_id}&limit=827')
        data=res.json()
        tracks=data.get('songs')
        if tracks:
            with codecs.open(os.path.dirname(os.path.abspath(__file__))+'/playlist_'+list_id+'.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, sort_keys=False, indent=None, ensure_ascii=False)
        ids=[]
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
    password=config.password
    print('开始登录')
    cm=CloudMusic(api,phone,password)
    uid=cm.login()
    if not uid:
        print('登录失败')
        exit(0)
    print('【uid=%s】'%uid)
    try:
        print('开始签到')
        cm.qiandao()
        print('开始处理歌单')
        #if int(time.strftime('%H'))<8:
            #网易云6点更新推荐 8点后处理避免将昨天的歌单放到今天的歌单里
        #    print('不到8点，不处理')
        #    exit(0)
        user_music_list = cm.getUserMusicList(uid)
        SYNC_LIST = {'[宝藏系女孩]':'Exotic', 
                  '[宝藏系男孩]':'Exotic Male', 
                  '[东方禅意]':'Chinese Folk', 
                  '[青春点唱机]':'80s', 
                  '[旧日金曲漫步]':'90s', 
                  '[牛奶泡泡浴]':'Lazy', 
                  '[爱的巴萨诺瓦]':'Bossa Nova', 
                  '[今夜晚点睡]':'Romance', 
                  '[浪漫婚礼专用]':'Sweet Love', 
                  '[阅读好时光]':'Reading', 
                  '[聚精会神]':'Concentration',
                  '[运动随身听]':'Sports',  
                  '[大自然纯音]':'Nature', 
                  '[古典歌剧典藏]':'Opera', 
                  '[开启学霸模式]':'Western Classical', 
                  '[放刺一周电音]':'Electronic', 
                  '[电音小情歌]':'Electronic Love', 
                  '[公路之歌]':'Roadtrip', 
                  '[放克复古派对]':'Funk', 
                  '华语私人定制':'Chinese',
                  '[粤语唱片行]':'Cantonese',
                  '[法语浪漫订制]':'French', 
                  '[一周韩语上新]':'Korean', 
                  '[韩系小甜歌]':'Korean Sweet', 
                  '日本流行精选':'Japanese', 
                  '[儿童趣味百科]':'Children Wiki', 
                  '[亲子玩耍时光]':'Children Joy', 
                  '[宝贝安全教育]':'Children Safety', 
                  '[亲子早教儿歌]':'Children Early Education', 
                  '[儿童诗词吟唱]':'Children Poems', 
                  '[亲子欢乐儿歌]':'Children Games'}
         # 虚位以待 深厚磁性男声
        for src_list_keyword,dst_list_name in SYNC_LIST.items():
            src_list_id = ""
            for list_name in user_music_list:
                if src_list_keyword in list_name:
                    src_list_id = user_music_list[list_name]
                    print('【源歌单已找到】%s' % str((src_list_id,list_name)) )
                    break
            if not src_list_id:
                print('【源歌单未找到】%s' % str((src_list_keyword,user_music_list)) )
                continue
            #src_list_music_ids = cm.getMusicListDetail(src_list_id)
            src_list_music_ids = cm.getMusicListTracks(src_list_id)
            print(f'〖源歌单列表({str(len(src_list_music_ids))})〗') #：{str(src_list_music_ids)}
            if dst_list_name in user_music_list:
                dst_list_id = user_music_list[dst_list_name]
                print('〖目标歌单已存在〗%s' % str((dst_list_id,dst_list_name)))
            else:
                dst_list_id = cm.createMusicList(dst_list_name)
                print('〖目标歌单已新建〗%s' % str((dst_list_id,dst_list_name)))
            #day_music_ids = cm.getDaySend()
            #dst_list_music_ids = cm.getMusicListDetail(dst_list_id)
            dst_list_music_ids = cm.getMusicListTracks(dst_list_id)
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
                    print(f'━━▶添加歌曲列表成功【{str(len(will_add_list))}】：{music_ids}')
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

