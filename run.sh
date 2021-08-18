#! /bin/sh

python3 terrascript-util.py

for d in infoblox/*/ ; do
    #echo "$d"
    cd $d
    terraform init
    terraform apply
    #terraform output -json | jq -r '@sh "export zoneid=\(.zone_ids.value)"'
    zoneid=`terraform output -raw zone_id`
    #echo $zoneid
    domain=`terraform output -raw domain_name`
    #echo $domain
    cd ../..
    aws route53 change-resource-record-sets --hosted-zone-id $zoneid  --change-batch file://mx/$domain.json
done

#cleanup
for d in infoblox/*/ ; do
    #rm -rf $d
done	
for f in mx/*.json ; do
    #rm -f $f
done
