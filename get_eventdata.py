import sys,os
from obspy.clients.fdsn import Client
from obspy.clients.fdsn.mass_downloader import CircularDomain, \
    Restrictions, MassDownloader
from obspy.clients.fdsn.header import URL_MAPPINGS

providers=list(URL_MAPPINGS.keys())

network="AM,G,CU,NU,SV,GI,OV,TC,AM"
channel="SH?,EH?,HH?,SN?,EN?,HN?"
maxradius = sys.argv[3]

client = Client(sys.argv[1])
cat = client.get_events(eventid=sys.argv[2],
                        includeallorigins=False, 
                        includeallmagnitudes=False, 
                        includearrivals=False)
print(cat)
origin_time = cat[0].preferred_origin().time
origin_latitude = cat[0].preferred_origin().latitude
origin_longitude = cat[0].preferred_origin().longitude

# Circular domain around the epicenter. This will download all data between
# 70 and 90 degrees distance from the epicenter. This module also offers
# rectangular and global domains. More complex domains can be defined by
# inheriting from the Domain class.
domain = CircularDomain(latitude=origin_latitude, 
                        longitude=origin_longitude,
                        maxradius=maxradius,
                        minradius=0.0)

restrictions = Restrictions(# Get data from 5 minutes before the event to one hour after the
                            # event. This defines the temporal bounds of the waveform data.
                            starttime=origin_time - 1 * 60,
                            endtime=origin_time + 5 * 60,
                            # Considering the enormous amount of data associated with continuous
                            # requests, you might want to limit the data based on SEED identifiers.
                            # If the location code is specified, the location priority list is not
                            # used; the same is true for the channel argument and priority list.
                            network=network, 
                            channel=channel)

# No specified providers will result in all known ones being queried.
mdl = MassDownloader(providers=providers)

# The data will be downloaded to the ``./waveforms/`` and ``./stations/``
# folders with automatically chosen file names.
mdl.download(domain, 
             restrictions,  
             mseed_storage="waveforms",
             stationxml_storage="stations")