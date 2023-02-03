#!/usr/bin/env seiscomp-python
import sys
from datetime import datetime

def getpicklog(f):
    if not os.path.exists(f):
        return []
    with open(f,'r') as content:
        picks = [line.strip().split() for line in content if " A " in line]
    for i,p in enumerate(picks):
        ct=p[-1].split('/')[-1].split('.')
        picks[i] += ['.'.join(p[2:6])]
        picks[i] += [datetime.strptime(p[0]+p[1]+'00000', '%Y-%m-%d%H:%M:%S.%f')]
        picks[i] += [datetime.strptime(ct[0]+ct[1], '%Y%m%d%H%M%S%f')]
    return picks

def getpickxml(f):
    ct =[]
    t=[]
    wf = []
    with open(f,'r') as content:
        for line in content:
            if "Z</creationTime>" in line:
                #<creationTime>2022-02-16T07:12:38.396655Z</creationTime>
                ct += [line.strip().split()[-1][14:39].replace('Z','0').replace('<','0')] 
            if "Z</value>" in line:
                #<value>2022-02-16T07:12:36.375Z</value>
                t += [line.strip().split()[-1][7:29].replace('Z','0').replace('<','0')]
            if "<pick publicID=" in line:
                #<pick publicID="20220216.071236.37-GI.SUCU..HNZ">
                wf += [line.strip().split()[-1].split('-')[-1][:-2]]
    picks = [[] for i,p in enumerate(t)]
    for i,p in enumerate(t):
        #print(wf[i],p+'0000',ct[i]+'0')
        picks[i] += [wf[i]]
        picks[i] += [datetime.strptime(p+'0000', '%Y-%m-%dT%H:%M:%S.%f')]
        picks[i] += [datetime.strptime(ct[i]+'0', '%Y-%m-%dT%H:%M:%S.%f')]
    return picks

import numpy,matplotlib.pyplot,os
matplotlib.use('Agg') 
def pickgraph(picks,xlim=None,save=None,mseedids=None,close=False):
    allpicks = []
    figdelay = 0
    for k in picks:
        allpicks+=picks[k]
    if mseedids is None:
        mseedids = list(numpy.sort(list(set([p[-3] for p in allpicks]))))
    if xlim is None:
        xlim = ([min([p[-1] for p in allpicks]),max([p[-2] for p in allpicks])])

    lines = list(set([k[0] for k in picks if len(picks[k])]))
    pipelines = list(set([k[1] for k in picks if len(picks[k])]))

    if len(allpicks)==0:
        print('No data')
        print(picks)
        return
    fig, axes = matplotlib.pyplot.subplots(nrows=1, ncols=len(lines), 
                                     sharex=True, sharey=True, 
                                     gridspec_kw={'wspace':0},
                                     constrained_layout=True,
                                     figsize=(1.5*10*len(lines),1.5*len(mseedids)*.1))

    for l,line in enumerate(lines):
        ax = axes
        if len(lines)>1:
            ax = axes[l]

        ax.tick_params(right=True, top=True,left=True, bottom=True,
                       labelbottom=True, labeltop=True,labelright=True, labelleft=True,
                       which='both')
        ax.xaxis.label.set_size('small')
        
        if l==0:
            ax.tick_params(labelright=False)
        elif l==len(lines)-1:
            ax.tick_params(labelleft=False)
        else:
            ax.tick_params(labelright=False,labelleft=False)
        ax.grid(b=True, which='major', color='gray', linestyle='dashdot', zorder=-999)
        ax.grid(axis='x', which='minor', color='beige',  ls='-', zorder=-999)

        ax.plot(numpy.nan,numpy.nan,'o',color='k',markerfacecolor='none',markeredgewidth=2,label='Arrival times')
        ax.plot(numpy.nan,numpy.nan,'+',color='k',markeredgewidth=2,label='Creation times')

        ax.set_yticks(range(len(mseedids)))
        ax.set_yticklabels(mseedids, fontsize='xx-small')
        ax.set_ylim([-0.5,len(mseedids)-.5])
        
        ax.xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
        ax.set_xlim([t for t in xlim])
            
        
        for i,pipeline in enumerate(pipelines):
            pick = [p for p in picks[(line,pipeline)] if p[-1]>xlim[0]if p[-1]<xlim[1] ]
            if not len(pick):
                continue

            ax.plot(numpy.nan,numpy.nan,'+',color='C%d'%i,label=pipeline)

            s = [(p[-1]-p[-2]).total_seconds() for p in pick]
            figdelay = max([figdelay, numpy.percentile(s,95)])
            y = [mseedids.index(p[-3]) for p in pick]
            opt={'y':y,
                 's':[((e+8)*8)**.8 for e in s],
                 'capstyle':'round',
                 'color':'C%d'%i}

            x = [p[-1] for p in pick ]
            if False:
                for k in range(8):
                    ax.scatter(x,**opt,marker='+',zorder=1,
                            linewidths=[(w/50+2)*k for w in s],
                            alpha=(8-k)/8)
            ax.scatter(x,**opt,marker='+',linewidth=1,zorder=1)

            x=[p[-2] for p in pick ]
            if False:
                for k in range(8):
                    ax.scatter(x,**opt,marker='+',zorder=1,
                            linewidths=[(w/50+2)*k for w in s],
                            alpha=(8-k)/8)
            ax.scatter(x,**opt,marker='o',facecolors='none',linewidth=1,zorder=2)
        
        for s in [3,10,30,100]:
            ax.scatter(numpy.nan,numpy.nan,s=((s+8)*8)**.8,marker='+',color='k',label='%s s delay'%s)

        ax.legend(title=line)
        ax.set_title(line)


    strxlim = [str(x) for x in xlim]
    figname=''
    for i in range(min([len(x) for x in strxlim])):
        if strxlim[0][i]!=strxlim[1][i]:
            break
        figname+=strxlim[0][i]
    fig.suptitle('Pick logs on %s (95%s within %.1f s)'%(figname,'%',figdelay))

    if save is not None:
        if '%' in save:
            save=save%(int((figdelay+5)/10)*10)
        if False:
            d=os.path.dirname(save)
            if not os.path.isdir(d):
                print('Making  %s...'%d)
                os.makedirs(d)
        print('Saving in %s...'%save)
        fig.savefig(save,
                    dpi=512/2, 
                    bbox_inches='tight', 
                    facecolor='none',
                    transparent=False)
    if close:
        matplotlib.pyplot.close(fig)
        return
    return fig     
    
picks={}
for host,alias,file in [tuple(arg.split(':')) for arg in sys.argv[1:]]:
    if 'xml' in file:
        picks[(host,alias)] = getpickxml(file)
    else:
        picks[(host,alias)] = getpicklog(file)

fig=pickgraph(picks,
              #xlim=[catalog[e].preferred_origin().time-60,
              #      catalog[e].preferred_origin().time+3*60],
              save='last.png',
              close=True)
