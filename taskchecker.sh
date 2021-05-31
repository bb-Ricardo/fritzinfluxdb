#!/bin/bash
fritztasks=($(service fritzinfluxdb status | awk '{ print $2 }'))
if [ ${fritztasks[4]} -lt 4 ]
then
	service fritzinfluxdb restart > /dev/null
fi
