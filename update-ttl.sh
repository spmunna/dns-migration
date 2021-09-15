#! /bin/sh

export IFS=","
hosted_zone_ids="Z0243949NVR9LVUYI2AX,Z0040812XL90VNTJJKSU"

for id in $hosted_zone_ids; do
#echo $id
python3 ttl.py "$id"
done

