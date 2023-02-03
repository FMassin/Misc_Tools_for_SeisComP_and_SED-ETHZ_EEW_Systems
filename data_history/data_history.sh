#!/bin/bash
set -x #echo on

for i in {0..312}
do
	E=$( date --date=$(( 7*$i ))"day ago" +%Y-%m-%d)
	B=$( date --date=$(( 7*($i + 10) ))" day ago" +%Y-%m-%d) 
	scquery $@ assoc_picks $B $E > ${B}_${E}.time.txt 
	scquery $@ delta_sta_net_mag_type $B $E > ${B}_${E}.amp.txt
done
