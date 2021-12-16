"""不打印日志版"""
import requests as r
import time
import config

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
        data=res.json()
        if data.get('code')==200:
            return True
        return False

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
        SYNC_LIST = {'[宝藏系女孩]':'Exotic','[东方禅意]':'Chinese Folk','[青春点唱机]':'80s','[旧日金曲漫步]':'90s','[爱的巴萨诺瓦]':'Bossa Nova','[今夜晚点睡]':'Romance','[法语浪漫订制]':'French','[一周韩语上新]':'Korean','日本流行精选':'Japanese'}
        for src_list_keyword,dst_list_name in SYNC_LIST.items():
            src_list_id = ""
            for list_name in user_music_list:
                if src_list_keyword in list_name:
                    src_list_id = user_music_list[list_name]
                    print('找到源歌单：%s' % str((src_list_id,list_name)) )
                    break
            if not src_list_id:
                print('无法找到源歌单：%s' % str((src_list_keyword,user_music_list)) )
                continue
            if dst_list_name in user_music_list:
                dst_list_id = user_music_list[dst_list_name]
                print('已有目标歌单：%s' % str((dst_list_id,dst_list_name)))
            else:
                dst_list_id = cm.createMusicList(dst_list_name)
                print('创建目标歌单：%s' % str((dst_list_id,dst_list_name)))
            #day_music_ids = cm.getDaySend()
            src_list_music_ids = cm.getMusicListDetail(src_list_id)
            dst_list_music_ids = cm.getMusicListDetail(dst_list_id)
            print('源歌单：%s' % str(src_list_music_ids))
            will_add_list = []
            for music_id in src_list_music_ids:
                if music_id in dst_list_music_ids:
                    pass
                else:
                    will_add_list.append(music_id)
            if len(will_add_list) > 0:
                music_ids = ','.join(will_add_list)
                res = cm.addMusicToList(dst_list_id, music_ids)
                if res:
                    print('添加歌曲列表：%s【成功】' % (music_ids))
                else:
                    print('添加歌曲列表：%s【失败】' % (music_ids))
    except:
        print('error')
