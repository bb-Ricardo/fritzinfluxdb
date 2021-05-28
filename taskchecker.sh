#!/bin/bash
tasks=$(ps -eLf | grep fritzinfluxdb | grep -wv grep | wc -l)
if [ $tasks -lt 4 ]
then
	service fritzinfluxdb restart > /dev/null
fi
