import terrascript
import terrascript.provider as provider
import terrascript.resource as resource

import csv
import os
import configparser
import json

parser = configparser.ConfigParser()
parser.read("migration.config")

for entry in os.scandir(parser.get("config", "csv_dir")):
    if (entry.path.endswith(".csv")) and entry.is_file():
            config = terrascript.Terrascript()
            config += provider.aws(version='~> 2.0', region=parser.get("config", "region"))
            config += terrascript.Output(
                "zone_id",
                value="${aws_route53_zone.main.zone_id}",
            )
            
            domainname = os.path.splitext(os.path.basename(entry.path))[0]
            
            config += terrascript.Output(
                "domain_name",
                value=domainname,
            )
            
            config += resource.aws_route53_zone('main',name=domainname)
            
            with open(entry.path) as csv_file:
                with open(parser.get("config", "mx_json_template"), 'r') as fpmxread:
                    mx_information = json.load(fpmxread)
                
                csv_reader = csv.reader(csv_file, delimiter=',')
                line_count = 0
                txtvaluelist = {}
                mxvaluelist = {}
                for row in csv_reader:
                    if line_count == 0:
                        line_count += 1
                    else:
                        line_count += 1
                        if row[0] == 'txtrecord':                      
                            txtvalue = row[3].replace('\"','')
                            
                            txtvalue = '"'+txtvalue+'"'
                            if row[1] not in txtvaluelist:
                                txtvaluelist[row[1]] = txtvalue
                            else:    
                                txtvaluelist[row[1]] += " " + txtvalue
                        if row[0] == 'cnamerecord':
                            config += resource.aws_route53_record('record_'+str(line_count),zone_id="${aws_route53_zone.main.zone_id}",name=row[1],type="CNAME",ttl=parser.get("config", "cname_ttl"),records=[row[3]])
                        if row[0] == 'hostrecord':
                            config += resource.aws_route53_record('record_'+str(line_count),zone_id="${aws_route53_zone.main.zone_id}",name=row[1],type="A",ttl=parser.get("config", "a_ttl"),records=[row[3]])
                        
                        if row[0] == 'mxrecord':
                            mxvalue = row[5] +" "+ row[3]
                            
                            if row[1] not in mxvaluelist:
                                mxvaluelist[row[1]] = mxvalue
                            else:
                                mxvaluelist[row[1]] += ','+mxvalue
                        if row[0] == 'arecord':
                            config += resource.aws_route53_record('record_'+str(line_count),zone_id="${aws_route53_zone.main.zone_id}",name=row[3],type="A",ttl=parser.get("config", "a_ttl"),records=[row[1]])

            for key in txtvaluelist:
                txtvaluelistitem = '"'+txtvaluelist[key]+'"'
                
                config += resource.aws_route53_record('record_'+str(line_count),zone_id="${aws_route53_zone.main.zone_id}",name=key,type="TXT",ttl=parser.get("config", "txt_ttl"),records=[txtvaluelistitem])
                line_count += 1

            mx_record_cnt = 0

            for key in mxvaluelist:
                mxvaluelistitem = mxvaluelist[key]
                if mx_record_cnt == 0:
                    mx_information["Changes"][mx_record_cnt]["ResourceRecordSet"]["Name"] = key
                    for substr in mxvaluelistitem.split(","):
                        mx_information["Changes"][mx_record_cnt]["ResourceRecordSet"]["ResourceRecords"].append({
                            "Value":substr
                        })
                else:
                    mx_information["Changes"].append({
                        "Action": "CREATE",
                        "ResourceRecordSet": {
                            "Name": key,
                            "Type": "MX",
                            "TTL": int(parser.get("config", "mx_ttl")),
                            "ResourceRecords": []
                        }
                    })    
                    for substr in mxvaluelistitem.split(","):
                        mx_information["Changes"][mx_record_cnt]["ResourceRecordSet"]["ResourceRecords"].append({
                            "Value":substr
                        })

                mx_record_cnt += 1
                line_count += 1
            
            with open(parser.get("config", "mx_json_dir")+"/"+domainname+".json", 'w') as fpmxwrite:
                json.dump(mx_information, fpmxwrite, indent=2)

            tfjsonfilename = parser.get("config", "csv_dir")+"/"+domainname+"/"+domainname+'.tf.json'
            if not os.path.exists(os.path.dirname(tfjsonfilename)):
                try:
                    os.makedirs(os.path.dirname(tfjsonfilename))
                except OSError as exc: # Guard against race condition
                    if exc.errno != errno.EEXIST:
                        raise

            with open(tfjsonfilename, 'wt') as fp:
                fp.write(str(config))
