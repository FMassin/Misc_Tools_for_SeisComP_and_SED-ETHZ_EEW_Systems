#!/usr/bin/env seiscomp-python
from asyncio import streams
import sys
from datetime import datetime

from matplotlib.ticker import Locator


class MinorSymLogLocator(Locator):
    """
    Dynamically find minor tick positions based on the positions of
    major ticks for a symlog scaling.
    """
    def __init__(self, linthresh):
        """
        Ticks will be placed between the major ticks.
        The placement is linear for x between -linthresh and linthresh,
        otherwise its logarithmically
        """
        self.linthresh = linthresh

    def __call__(self):
        'Return the locations of the ticks'
        majorlocs = self.axis.get_majorticklocs()

        # iterate through minor locs
        minorlocs = []

        # handle the lowest part
        for i in range(1, len(majorlocs)):
            majorstep = majorlocs[i] - majorlocs[i-1]
            if abs(majorlocs[i-1] + majorstep/2) < self.linthresh:
                ndivs = 10
            else:
                ndivs = 9
            minorstep = majorstep / ndivs
            locs = numpy.arange(majorlocs[i-1], majorlocs[i], minorstep)[1:]
            minorlocs.extend(locs)

        return self.raise_if_exceeds(numpy.array(minorlocs))

    def tick_values(self, vmin, vmax):
        raise NotImplementedError('Cannot get tick locations for a '
                                  '%s type.' % type(self))


def get_query(f='/Users/fred/Documents/Data/ATTAC/pick-amp_history/ineter/2021-11-09_2022-01-18.time.txt'):
    if not os.path.exists(f):
        return {}
    with open(f,'r') as content:
        streams = [line.strip().split('|') for line in content]
    #AM | RB213 | 00 | EHZ | P | automatic | Trigger | 17  | 1.840531431545091       | -9.263270378           | 9.15668869              | 11.2181818182       | -1.000000           | 44.000000       | 2021-12-01 01:56:53 | 2022-01-24 20:05:03
    #CM | SJC   | 00 | BHZ | NULL             | MLv | 121  | 0.09688225136363632     | -1.1566755840000003    | 1.2420566610000003      | 2021-11-23 07:09:31 | 2022-01-31 03:34:17
    delay={}
    residual={}
    endtime={}
    starttime={}
    for stream in streams:
        if len(stream)<7:
            continue

        if len(stream)==16:
            k = '.'.join(stream[:7]).replace(' ','')
            if 'NULL' in stream[8]:
                residual[k] = numpy.nan
            else:
                residual[k] = float(stream[8])
            delay[k] = float(stream[11])
        else:
            k = '.'.join(stream[:6]).replace(' ','')
            residual[k] = float(stream[7])

        endtime[k] = datetime.strptime(stream[-1].replace(' ','')+'.00000', '%Y-%m-%d%H:%M:%S.%f')
        starttime[k] = datetime.strptime(stream[-2].replace(' ','')+'.00000', '%Y-%m-%d%H:%M:%S.%f')

    return {'residual':residual,
            'delay':delay,
            'starttime':starttime,
            'endtime':endtime}

import glob
def get_queries(f='/Users/fred/Documents/Data/ATTAC/pick-amp_history/ovsicori/*time.txt'):
    data = {d:{} for d in ['residual','delay','starttime','endtime']}
    for file in glob.glob(f):
        tmp=get_query(file)
        for k in tmp:
            for s in tmp[k]:
                if s in data[k]:
                    data[k][s]+=[tmp[k][s]]
                else:
                    data[k][s]=[tmp[k][s]]
    return data

def get_data(times='/Users/fred/Documents/Data/ATTAC/pick-amp_history/ovsicori/*time.txt',
             amplitudes='/Users/fred/Documents/Data/ATTAC/pick-amp_history/ovsicori/*amp.txt'):
    return {'times': get_queries(times),
            'amplitudes':get_queries(amplitudes)}


import numpy,matplotlib.pyplot,os
def make_axes():
    fig, axes = matplotlib.pyplot.subplots(nrows=3, ncols=1, 
                                sharex=True, sharey=False, 
                                gridspec_kw={'hspace':0},
                                constrained_layout=True,
                                figsize=(16,10)
                                )

    for l,ax in enumerate(axes):
        ax.tick_params(labelright=True,labelleft=True,labeltop=True,labelbottom=True)
        if l==0:
            ax.tick_params(labelbottom=False)
        elif l==2:
            ax.tick_params(labeltop=False)
        else:
            ax.tick_params(labelbottom=False,labeltop=False)

        ax.tick_params(right=True, top=True,left=True, bottom=True, which='both')        
        ax.grid(b=True, which='major', color='gray', linestyle='dashdot', zorder=-999)
        ax.grid(axis='x', which='minor', color='beige',  ls='-', zorder=-999)
        ax.grid(axis='y', which='minor', color='beige',  ls='-', zorder=-999)

        #ax.xaxis.label.set_size('small')

        #ax.plot(numpy.nan,numpy.nan,'o',color='k',markerfacecolor='none',markeredgewidth=2,label='Arrival times')
        #ax.plot(numpy.nan,numpy.nan,'+',color='k',markeredgewidth=2,label='Creation times')

        #ax.set_yticks(range(len(mseedids)))
        #ax.set_yticklabels(mseedids, fontsize='xx-small')
        #ax.set_ylim([-0.5,len(mseedids)-.5])
        
        ax.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
        ax.xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
        
        #ax.set_xlim([t for t in xlim])
        #ax.legend(title=line)
    return axes 

    
def plot_datahist(data,
                  color='C0',
                  whitelist=None,
                  axes=None,
                  show=True,
                  save=None,
                  close=True):
    #
    # ADD legend
    # ADD strong motion amplitude
    #
    fake=None
    if axes is None:
        fake=[numpy.nan,numpy.nan]
        axes=make_axes()
        #axes[0].figure.suptitle('Data history')

    timesamples = [t.timestamp() for k in data['times']['endtime'] for t in data['times']['endtime'][k] ]
    timesamples = numpy.arange(min(timesamples),max(timesamples),14*24*60*60)
    ny = timesamples*0
    nysm = timesamples*0
    ns = [[] for x in timesamples]
    nsm = [[] for x in timesamples]
    for i,x2 in enumerate(timesamples):
        if i==0:
            continue
        x1=timesamples[i-1]
        for datatype in ['times','amplitudes']:
            for k in data[datatype]['residual']:
                station='.'.join(k.split('.')[:2]) 
                instrument=k.split('.')[3][:2]
                if not len(data[datatype]['endtime'][k]):
                    continue
                for x,t in enumerate(data[datatype]['endtime'][k]):
                    st=data[datatype]['starttime'][k][x].timestamp()
                    et=t.timestamp()
                    if ((x1<et and et<x2) or (x1<st and st<x2)) and (station not in ns[i]):
                        ny[i] += 1
                        ns[i] += [station]
                        if instrument[1] in 'NG':
                            nysm[i] += 1
                            nsm[i] += ['%s.%s'%(station,instrument)]
                        break
                

    #print(len(list(set([s for n in ns for s in n]))))
    #print(list(set([s for n in nsm for s in n])))
    axes[0].plot([datetime.fromtimestamp(t) for t in timesamples],ny,color=color)
    axes[0].plot([datetime.fromtimestamp(t) for t in timesamples],nysm,color=color,ls=':')
    axes[0].set_ylabel('Number of active stations')
    if fake is not None:
        axes[0].plot(fake,fake,color='k',label='All stations')
        axes[0].plot(fake,fake,color='k',ls=':',label='Strong motion stations')
        axes[0].legend(title='A')

    if False:
        for k in data['times']['residual']:
            x=data['times']['endtime'][k]
            y=data['times']['residual'][k]
            y=[y[i] for i in numpy.argsort(x)]
            x=[x[i] for i in numpy.argsort(x)]
            axes[1].plot(x,y,alpha=0.1,color=color)


    for dt,datatype in enumerate(['times','amplitudes']):
        ny = timesamples*0
        nysm = timesamples*0
        y = [[] for x in timesamples]
        ysm = [[] for x in timesamples]
        ns = [[] for x in timesamples]
        nsm = [[] for x in timesamples]
        for i,x2 in enumerate(timesamples):
            if i==0:
                continue
            x1=timesamples[i-1]
            for k in data[datatype]['residual']:
                station='.'.join(k.split('.')[:2]) 
                instrument=k.split('.')[3][:2]
                if not len(data[datatype]['endtime'][k]):
                    continue
                for x,t in enumerate(data[datatype]['endtime'][k]):
                    st=data[datatype]['starttime'][k][x].timestamp()
                    et=t.timestamp()
                    if ((x1<et and et<x2) or (x1<st and st<x2)) and (station not in ns[i]):
                        ny[i] += 1
                        y[i] += [data[datatype]['residual'][k][x]]
                        ns[i] += [station]
                        if instrument[1] in 'NG':
                            nysm[i] += 1
                            ysm[i] += [data[datatype]['residual'][k][x]]
                            nsm[i] += ['%s.%s'%(station,instrument)]
                        break
        for i,x in enumerate(y):
            try:
                y[i]=numpy.percentile(y[i],50)
            except:
                y[i]=numpy.nan
            try:
                ysm[i]=numpy.percentile(ysm[i],50)
            except:
                ysm[i]=numpy.nan
        axes[2].plot([datetime.fromtimestamp(t) for t in timesamples],y,color=color,ls='-:'[dt])
        #axes[2].plot([datetime.fromtimestamp(t) for t in timesamples],ysm,color=color,ls=':')

    axes[2].set_yscale('symlog', linthresh=.1,linscale=0.5)
    axes[2].yaxis.set_minor_locator(MinorSymLogLocator(.1))
    axes[2].set_ylabel('Station residual (travel time seconds, magnitude units)')

    if fake is not None:
        axes[2].plot(fake,fake,color='k',label='Travel times')
        axes[2].plot(fake,fake,color='k',ls=':',label='Station magnitudes')
        axes[2].legend(title='C')

    if False:
        for k in data['times']['delay']:
            x=data['times']['endtime'][k]
            y=data['times']['delay'][k]
            y=[y[i] for i in numpy.argsort(x)]
            x=[x[i] for i in numpy.argsort(x)]
            axes[2].plot(x,y,alpha=0.1,color=color)

    ny = timesamples*0
    nysm = timesamples*0
    y = [[] for x in timesamples]
    ysm = [[] for x in timesamples]
    ns = [[] for x in timesamples]
    nsm = [[] for x in timesamples]
    for i,x2 in enumerate(timesamples):
        if i==0:
            continue
        x1=timesamples[i-1]
        for datatype in ['times']:#,'amplitudes']:
            for k in data[datatype]['delay']:
                station='.'.join(k.split('.')[:2]) 
                instrument=k.split('.')[3][:2]
                if not len(data[datatype]['endtime'][k]):
                    continue
                for x,t in enumerate(data[datatype]['endtime'][k]):
                    st=data[datatype]['starttime'][k][x].timestamp()
                    et=t.timestamp()
                    if ((x1<et and et<x2) or (x1<st and st<x2)) :#and (station not in ns[i]):
                        ny[i] += 1
                        y[i] += [data[datatype]['delay'][k][x]]
                        ns[i] += [station]
                        if instrument[1] in 'NG':
                            nysm[i] += 1
                            ysm[i] += [data[datatype]['delay'][k][x]]
                            nsm[i] += ['%s.%s'%(station,instrument)]
                        break
    for i,x in enumerate(y):
        try:
            y[i]=numpy.percentile(y[i],15)
        except:
            y[i]=numpy.nan
        try:
            ysm[i]=numpy.percentile(ysm[i],10)
        except:
            ysm[i]=numpy.nan
    axes[1].plot([datetime.fromtimestamp(t) for t in timesamples],y,color=color)
    axes[1].plot([datetime.fromtimestamp(t) for t in timesamples],ysm,color=color,ls=':')

    axes[1].set_yscale('symlog', linthresh=10,linscale=2)
    axes[1].yaxis.set_minor_locator(MinorSymLogLocator(10))
    axes[1].set_ylabel('Station trigger delay (s)')

    if fake is not None:
        axes[1].plot(fake,fake,color='k',label='All stations')
        axes[1].plot(fake,fake,color='k',ls=':',label='Strong motion stations')
        axes[1].legend(title='B')

    if save is not None:
        print('Saving in %s...'%save)
        axes[0].figure.savefig(save,
                    dpi=512/2, 
                    bbox_inches='tight', 
                    facecolor='none',
                    transparent=False)
        
    if close:
        matplotlib.pyplot.close(axes[0].figure)
        return
    return axes 

def datafilter(d,
               whitelist=None, 
               blacklist=['.AIC','.manual']):
    tmp={}
    streams=[]
    meta=[]
    rstreams=[]
    rmeta=[]
    for datatype in d:
        tmp[datatype]={}
        for metrics in d[datatype]:
            tmp[datatype][metrics]={}
            for stream in d[datatype][metrics]:
                ignore=False
                if blacklist is not None:
                    for b in blacklist:
                        if b in stream:
                            ignore=True
                if whitelist is not None:
                    if True not in [ w == stream[:len(w)] for w in whitelist ]:
                        ignore=True
                rstreams+=['.'.join(stream.split('.')[:4])] 
                rmeta+=['.'.join(stream.split('.')[4:])] 
                if not ignore:
                    tmp[datatype][metrics][stream]=d[datatype][metrics][stream]  
                    streams+=['.'.join(stream.split('.')[:4])] 
                    meta+=['.'.join(stream.split('.')[4:])] 

    #print('raw:',list(set(rstreams)),list(set(rmeta)))
    #print('filtered:',list(set(streams)),list(set(meta)))

    return tmp

def testdata(dirs=['/Users/fred/Documents/Data/ATTAC/pick-amp_history/ineter/',
               '/Users/fred/Documents/Data/ATTAC/pick-amp_history/marn/',
               '/Users/fred/Documents/Data/ATTAC/pick-amp_history/ovsicori/',
               '/Users/fred/Documents/Data/ATTAC/pick-amp_history/insivumeh/']):
    return [get_data('%s/*time.txt'%d,'%s/*amp.txt'%d) for d in dirs]

def test(data,
         whitelists=[['NU.'],['SV.','SN.'],['OV.'],['GI']],
         labels=['INETER','MARN','OVSICORI-UNA','INSIVUMEH'],
         save='test.png'):
    
    for i,d in enumerate(data):
        tmp = datafilter(d,whitelist=whitelists[i])
        if i==0:
            axes=plot_datahist(tmp,color='C%d'%i,save=None,close=False)
        elif i==len(data)-1:
            plot_datahist(tmp,color='C%s'%i,save=save,axes=axes)
        else:
            plot_datahist(tmp,color='C%s'%i,save=None,axes=axes,close=False)

    fake=[numpy.nan,numpy.nan]

    h = []
    for i,label in enumerate(labels):
        h+=[axes[0].plot(fake,fake,color='C%d'%i,label=label)[0]]
    axes[0].figure.legend(h,labels,
                          ncol=len(labels),
                          loc="upper center")
    
    print('Saving in %s...'%save)
    axes[0].figure.savefig(save,
                dpi=512/2, 
                bbox_inches='tight', 
                #facecolor='none',
                transparent=False)
    
    return axes[0].figure
