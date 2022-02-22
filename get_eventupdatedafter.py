
from obspy import UTCDateTime

def get_eventsupdateafter(client=None,
               updateafter=None,
               updatebefore=None,
               checkupdateafter=None,
               checkupdatebefore=None,
               **opts):
    quickopts = opts
    quickopts['includearrivals']=False
    quickopts['starttime']=checkupdateafter
    quickopts['endtime']=checkupdatebefore
    tmp = client.get_events(**quickopts)
    evts=[]
    opts['minlatitude']=None
    opts['minlongitude']=None
    opts['maxlatitude']=None
    opts['maxlongitude']=None
    for ev in tmp:
        times = [o.creation_info.creation_time for o in ev.origins]
        times += [m.creation_info.creation_time for m in ev.magnitudes]
        if updateafter is not None and updateafter>max(times):
            continue
        eventid=str(ev.resource_id)#.split('eventid=')[-1].split('&')[0]
        o=ev.preferred_origin()
        opts['starttime']=str(o.time-1)[:19]
        opts['endtime']=str(o.time+1)[:19]
        opts['latitude']=o.latitude
        opts['longitude']=o.longitude
        opts['maxradius']=0.1
        print('Get:',ev.short_str(),'|',eventid,'\nLast mod:',max(times),'is after:',updateafter)
        evts+=client.get_events(**opts).events
    tmp.events = evts
    return tmp

import obspy.clients.fdsn.client 
def testget_events(client=obspy.clients.fdsn.client.Client('INGV'),
                   limit=3,
                   updateafter=UTCDateTime()-4*43200,
                   checkupdateafter=UTCDateTime()-8*43200,
                   **moreopts):
    opts={'client':client,
          'limit':limit,
          'updateafter':updateafter,
          'checkupdateafter':checkupdateafter}
    print(get_eventsupdateafter(**opts,**moreopts))

