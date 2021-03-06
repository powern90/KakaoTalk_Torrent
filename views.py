from bs4 import BeautifulSoup
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bot.settings")
import django
django.setup()
from torrent.models import TorData
import json
import datetime
import requests
import urllib


TM_HOST = 'kkhnas.gq:9091'
TM_IDPW = 'powern90:awardsw3237'
SAVE_DAYS = 30
TOR_PAGE_URL_720p = 'https://torrenthaja.com/bbs/search.php?search_flag=search&stx=720p+NEXT&page=1'
TOR_PAGE_URL_1080p = 'https://torrenthaja.com/bbs/search.php?search_flag=search&stx=1080p+NEXT&page=1'

def keyboard(request):
    return JsonResponse({
            'type' : 'buttons',
                'buttons' : ['토렌트 검색','날씨 확인']
            })


@csrf_exempt
def first(request):
    message = ((request.body).decode('utf-8'))
    return_json_str = json.loads(message)
    return_str = return_json_str['content']
    return_id = return_json_str['user_key']

    info_dict = get_info(return_id, return_str)

    #검색리스트에 명령어가 있으면
    if return_str in info_dict['search_list']:

        #일반유저인지 확인
        if info_dict['user'] == 'False':
            found_one = TorData.objects.filter(title=return_str, resolution='720p')

            #이미 받은건지 확인
            if found_one[0].exist == True:
                return JsonResponse({
                        'message': {
                                'text': '이미 다운로드된 파일입니다.'
                            },
                                'keyboard': {
                                'type':'buttons',
                                'buttons' : ['토렌트 검색','날씨 확인']
                            }
                        })

            #받은게 아니면
            else:
                command = ' transmission-remote ' +  TM_HOST + ' -n ' + TM_IDPW + ' -a ' + found_one[0].magnet
                os.system(command)
                found_one.update(exist=True, req_id=return_id, down_date=datetime.datetime.now())
                return JsonResponse({
                        'message': {
                                'text': '다운로드를 시작합니다.'
                            },
                        'keyboard': {
                                'type':'buttons',
                                'buttons' : ['토렌트 검색','날씨 확인']
                            }
                        })

        #특수유저
        else:
            found_one = TorData.objects.filter(title=return_str, resolution='1080p')
            return JsonResponse({
                    'message': {
                        'text': found_one[0].magnet
                            },
                    'keyboard': {
                            'type':'buttons',
                        'buttons' : ['토렌트 검색','날씨 확인']
                        }
                    })



    #토렌트 검색으로 왔을때
    elif return_str == '토렌트 검색':
        return JsonResponse({
                'message': {
                        'text': "검색어를 입력해주세요"
                    },
                'keyboard': {
                        'type': 'text'
                    }
                })



    #날씨확인으로 왔을때
    elif return_str == '날씨 확인':
        return JsonResponse({
                'message': {
                        'text': "준비중 입니다."
                        },
                    'keyboard': {
                        'type':'buttons',
                        'buttons' : ['토렌트 검색','날씨 확인']
                        }
                    })

    #토렌트 파일검색
    else:
        if info_dict['user'] == 'False':
            found_list = search(return_str, '720p')
        else:
            found_list = search(return_str, '1080p')
        info_dict['search_list'] = found_list

        #못찾았을때
        if found_list.__len__() == 0:
            return JsonResponse({
                    'message': {
                        'text': "검색어를 찾지못했습니다."
                        },
                    'keyboard': {
                        'type':'buttons',
                        'buttons' : ['토렌트 검색','날씨 확인']
                        }
                    })
        #찾았을 때
        else:
            save_info(return_id, info_dict)
            return JsonResponse({
                    'message': {
                        'text':'다운받을 파일을 선택해 주세요'
                        },
                    'keyboard': {
                        'type':'buttons',
                        'buttons':found_list
                        }
                    })



def del_old(request):
    item = TorData.objects.exclude(date__lte=datetime.datetime.today(), date__gt=datetime.datetime.today()-datetime.timedelta(days=SAVE_DAYS))
    item.delete()
    return JsonResponse({})



def parse_list(request):
    ori_list = TorData.objects.all().values('title')
    data = []
    for item in ori_list:
        data.append(item['title'])


    #720p 가져오기
    req = urllib.request.Request(TOR_PAGE_URL_720p, headers={'User-Agent': 'Mozilla/5.0'})
    response = urllib.request.urlopen(req).read()
    text = response.decode('utf-8')
    soup = BeautifulSoup(text, 'html.parser')
    my_list = soup.find_all("tr")[1:]
    link_list = []
    for item in my_list:
        tmp = item.findChildren(recursive=False)[1].findChildren(recursive=False)[0].findChildren(recursive=False)[0].get('href')
        text = tmp.replace('./board.', 'https://torrenthaja.com/bbs/board.')
        link_list.append(text)
    send_dic = {}
    for item in link_list:
        try:
            req = urllib.request.Request(item, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req).read()
            text = response.decode('utf-8')
            soup = BeautifulSoup(text, 'html.parser')
            title = str(soup.find('h4').find_all(text=True)[1])
            if title in data:
                continue
            try:
                send_dic[title]
            except:
                magnet = 'magnet:?xt=urn:btih:' + soup.find('button', class_='btn btn-success btn-xs').get('onclick')[13:-3]
                send_dic[title]=magnet
                print(title)
        except:
            continue

    for t, l in send_dic.items():
        TorData(title=t, magnet=l, date=datetime.datetime.now(), resolution='720p').save()


    #1080p가져오기
    send_dic = {}
    req = urllib.request.Request(TOR_PAGE_URL_1080p, headers={'User-Agent': 'Mozilla/5.0'})
    response = urllib.request.urlopen(req).read()
    text = response.decode('utf-8')
    soup = BeautifulSoup(text, 'html.parser')
    my_list = soup.find_all("tr")[1:]
    link_list = []
    for item in my_list:
        tmp = item.findChildren(recursive=False)[1].findChildren(recursive=False)[0].findChildren(recursive=False)[0].get('href')
        text = tmp.replace('./board.', 'https://torrenthaja.com/bbs/board.')
        link_list.append(text)
    for item in link_list:
        try:
            req = urllib.request.Request(item, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req).read()
            text = response.decode('utf-8')
            soup = BeautifulSoup(text, 'html.parser')
            title = str(soup.find('h4').find_all(text=True)[1])
            if title in data:
                continue
            try:
                send_dic[title]
            except:
                magnet = 'magnet:?xt=urn:btih:' + soup.find('button', class_='btn btn-success btn-xs').get('onclick')[13:-3]
                send_dic[title]=magnet
                print(title)
        except:
            continue



    for t, l in send_dic.items():
        TorData(title=t, magnet=l, date=datetime.datetime.now(), resolution='1080p').save()
    return JsonResponse(send_dic)



def search(keyword, resolution):
    ori_list = TorData.objects.filter(resolution=resolution).values('title')
    data = []
    for item in ori_list:
        data.append(item['title'])
    found_list = []
    for item in data:
        if keyword in item:
            found_list.append(item)
    return found_list


def get_info(id, msg):
    with open('/home/ubuntu/Django/torrent/info.json', 'r+', encoding="utf-8") as info:
        read = info.read()
        try:
            data = json.loads(read)
        except:
            data = {}
        try:
            return_info = data[id]
            return_info['last_msg'] = msg
        except:
            data[id] = {'downloading': False, 'search_list': [], 'last_msg': msg, 'user': 'False'}
            return_info = data[id]

        info.seek(0)
        info.truncate()
        json.dump(data, info, ensure_ascii=False, indent="\t")
    return return_info


def save_info(id,dict):
    with open('/home/ubuntu/Django/torrent/info.json', 'r+', encoding="utf-8") as info:
        read = info.read()
        try:
            data = json.loads(read)
        except:
            data = {}
        data[id] = dict
        info.seek(0)
        info.truncate()
        json.dump(data, info, ensure_ascii=False, indent="\t")