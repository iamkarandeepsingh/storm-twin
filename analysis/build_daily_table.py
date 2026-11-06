import json,collections as C
from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo
TZ=ZoneInfo('America/Toronto')
D='data/raw/'
L=lambda f:json.load(open(D+f+'.json'))
def pu(s): return datetime.fromisoformat(s.replace('Z','+00:00'))
das=L('DeviceAssignment')
def truck_of(dev,t):
    for a in das:
        if a['device']['id']==dev and pu(a['activeFrom'])<=t<pu(a['activeTo']): return a['vehicleName']
# daily table: (truck, local date) -> readings
rows=C.defaultdict(dict)
for s in L('StatusData'):
    t=pu(s['dateTime']); tr=truck_of(s['device']['id'],t)
    rows[(tr,t.astimezone(TZ).date().isoformat())][s['diagnostic']['id'].replace('Diagnostic','').replace('Id','')]=s['data']
    rows[(tr,t.astimezone(TZ).date().isoformat())]['t']=t.astimezone(TZ).strftime('%H:%M')
