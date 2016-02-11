from pylab import *
import numpy as na
import pandas as pd
import matplotlib.font_manager
import csv
import sys
import re
import os
from distutils.dir_util import copy_tree
from xml.etree.ElementTree import ElementTree

reload(sys)
sys.setdefaultencoding('utf-8')
matplotlib.style.use('ggplot')



def percentile(n):
	def percentile_(x):
		return np.percentile(x, n)
	percentile_.__name__ = 'percentile_%s' % n
	return percentile_
  
def mask(df, f):
  return df[f(df)]

def getIndex(item):
	print item
	return int(re.search('(\d+)/', item[0]).group(1))		
	
def ord_to_char(v, p=None):
	return chr(int(v))

jtl_files = []
releases = []

builds_dir=sys.argv[1]
report_dir=sys.argv[2]


#builds_dir="C:\\Python27\\FoE\\"
#report_dir="C:\\Python27\\FoE\\"


print "builds_dir: " + builds_dir
print "Report dir: " + report_dir

  
build_xml = ElementTree()
for root, dirs, files in os.walk(builds_dir):
	for file in files:
		if file.endswith(".jtl"): 
			print file
			build_parameters = []
			displayName = "unknown"
			monitoring_data =  os.path.join(root.replace('JMeterCSV','').replace('performance-reports',''), "monitoring.data")  
			build_xml_path = os.path.join(root.replace('JMeterCSV','').replace('performance-reports',''), "build.xml")	   
			print monitoring_data
			print build_xml_path
			if os.path.isfile(build_xml_path):				
				build_xml.parse(build_xml_path)
				build_tag = build_xml.getroot()
			   
				for params in build_tag:
					if params.tag == 'actions':
						parameters = params.find('.//parameters')
						for parameter in parameters:
							name = parameter.find('name')
							value = parameter.find('value')
							build_parameters.append([name.text,value.text])
						print build_parameters
					elif params.tag == 'displayName':
						displayName = params.text
						print displayName

						
			if "Performance_HTML_Report" not in os.path.join(root, file):									   
				jtl_files.append([os.path.join(root, file),monitoring_data,displayName, build_parameters])

			  
jtl_files = sorted(jtl_files, key=getIndex,reverse=True)

print jtl_files
releases.sort();

print releases
  
dateconv = np.vectorize(datetime.datetime.fromtimestamp)
  

aggregate_table='aggregate_table' 
monitor_table='monitor_table'
if not os.path.exists(report_dir + 'pics'):
	os.makedirs(report_dir + 'pics')


report_html = report_dir + 'report.html' 

print "Try to copy resources dir to report directory: " + report_dir

fromDirectory = "/home/report_gen/resourses/"
toDirectory = report_dir

copy_tree(fromDirectory, toDirectory + "/resourses/")
  
print "Trying to open CSV-files"
  
dataframes = [pd.read_csv(jtl_files[i][0],index_col=0) for i in xrange(0,len(jtl_files))]



print "Trying to generate HTML-report: %s." % report_html
htmlfile = open(report_html,"w")
  
  
  
htmlfile.write("""<!DOCTYPE html>
<html>
<head>
<title>Performance Test report</title>
<link rel="stylesheet" type="text/css" href="./resourses/main.css">
<link rel="stylesheet" type="text/css" href="./resourses/blue/style.css">
<link rel="stylesheet" type="text/css" href="./resourses/jquery-ui.css">
<script src='./resourses/jquery-1.11.3.min.js'></script>
<script src='./resourses/jquery-ui.js'></script>
<script src='./resourses/jquery.elevatezoom.js'></script>
<script src='./resourses/jquery.tablesorter.js'></script>
<script>
  $(function() {
	$( "#tabs" ).tabs();
  });
   $(document).ready(function() 
	{ 
		$("#myTable").tablesorter(); 
	} 
   ); 
	 $(document).ready(function() 
	{ 

	var allElements = document.getElementsByTagName("table");
	for (var i = 0, n = allElements.length; i < n; ++i) {
		var el = allElements[i];		
		if (el.id) {
		 $('#' + el.id).tablesorter(); 
		}
		
	}
		
	} 
   ); 
</script>
</head>
<body>""")
agg = {}
mon = {}

rtot_over_releases = [];
cpu_over_releases = [];

file_index = 0
for df in dataframes:
	df.columns = ['average', 'URL','responseCode','success','threadName','failureMessage','grpThreads','allThreads']
	#convert timestamps to normal date/time
	df.index=pd.to_datetime(dateconv((df.index.values/1000)))
	num_lines = df['average'].count()
	print "Number of lines in file 1: %d." % num_lines
	


	byURL = df.groupby('URL') # group date by URLs  
	agg[file_index] = byURL.aggregate({'average':np.mean}).round(1)
	if file_index != 0:
		agg[file_index]['average-diff'] = dataframes[0].groupby('URL').average.mean().round(1)-dataframes[file_index].groupby('URL').average.mean().round(1)
	agg[file_index]['median'] = byURL.average.median().round(1)
	if file_index != 0:
		agg[file_index]['median-diff'] = dataframes[0].groupby('URL').average.median().round(1)-dataframes[file_index].groupby('URL').average.median().round(1)  
	agg[file_index]['75_percentile'] = byURL.average.quantile(.75).round(1)
	agg[file_index]['90_percentile'] = byURL.average.quantile(.90).round(1)
	agg[file_index]['99_percentile'] = byURL.average.quantile(.99).round(1)
	agg[file_index]['maximum'] = byURL.average.max().round(1)
	agg[file_index]['minimum'] = byURL.average.min().round(1)
	agg[file_index]['count'] = byURL.success.count().round(1)
	if file_index != 0:
		agg[file_index]['count-diff'] = dataframes[0].groupby('URL').success.count().round(1)-dataframes[file_index].groupby('URL').success.count().round(1)
	agg[file_index]['%_errors'] = ((1-df[(df.success == True)].groupby('URL')['success'].count()/byURL['success'].count())*100).round(1)
	if file_index != 0:
		agg[file_index]['%_errors_diff'] = (((1-dataframes[0][(dataframes[0].success == True)].groupby('URL').success.count()/dataframes[0].groupby('URL').success.count())*100)-((1-dataframes[file_index][(dataframes[file_index].success == True)].groupby('URL').success.count()/dataframes[file_index].groupby('URL').success.count())*100)).round(1)
	target_csv = report_dir +"pics/"+aggregate_table+str(file_index)+'.csv'
	
	print "Trying to save aggregate table to CSV-file: %s." % target_csv
	
	fig = plt.figure(figsize=(9,7))
	ax1 = fig.add_subplot(111)
	rtot_over_releases.append([jtl_files[file_index][2],agg[file_index].average.mean(),agg[file_index].average.median()])
	agg[file_index].to_csv(target_csv, sep=',')
	file_index += 1
   
		

	
	
htmlfile.write("""<div id="tabs">
  <ul>""")

htmlfile.write("""<li><a href='Overall' style="background-color:#FF9999">Overall</a></li>""")	  
  
for num in range(0,file_index):
	htmlfile.write("<li><a href='#tabs-")
	htmlfile.write(str(num))
	if num == 0:
		if jtl_files[num][2]!="unknown":
			htmlfile.write("'>"+jtl_files[num][2]+" (current)</a></li>")
		else:
			htmlfile.write("'>CURRENT</a></li>")
	else:
		htmlfile.write("'>vs. "+jtl_files[num][2].replace(u'\u200b', '*')+"</a></li>")
		
	
htmlfile.write("</ul>")
  
# Open the CSV file for reading
  
for num in range(0,file_index):
	htmlfile.write("""<div id="tabs-""")
	htmlfile.write(str(num))
	htmlfile.write("""">""")

	htmlfile.write('<ul id="vert_menu"><li><a href="#cpugraphs'+str(num)+'" class="current">cpu graphs</a><a href="#overallgraphs'+str(num)+'" class="current">overall graphs</a><a href="#actiongraphs'+str(num)+'" class="current">action graphs</a></li></ul>');
	rownum = 0
	htmlfile.write('<div class="datagrid" >')
	htmlfile.write('<table id="Table'+ str(num) +'" class="tablesorter">')
	target_csv = report_dir +"pics/"+aggregate_table+str(num)+'.csv'
	reader = csv.reader(open(target_csv))
	for row in reader: # Read a single row from the CSV file
	# write header row. assumes first row in csv contains header
		if rownum == 0:
			htmlfile.write('<thead><tr>') # write <tr> tag
			for column in row:
				if "URL" not in column and "diff" not in column and "count" not in column and "errors" not in column :
					column = column + " (ms)"
				htmlfile.write('<th>' + column + '</th>')
			htmlfile.write('</tr></thead>')
	  
		  #write all other rows	
		else:
			if rownum%2 == 0:
				htmlfile.write('<tr class="alt">')
			else:
				htmlfile.write('<tr>')
			row_value = [0 for i in xrange(15)]
			check_col = 0	
			for column in row:
				c_value = 0
				if check_col > 0:
					try:
						c_value = float(column)
					except ValueError,e:
						print "error",e,column
						c_value = 0
					
					row_value[check_col]=c_value		 
						 
				if (check_col==2 or check_col==4 or check_col==13) and num != 0:#diffs
					s = ""
					d = ""
					if(check_col==2 or check_col==4):
						d = " ms"
						if row_value[check_col] > 0:
							s = " +"
					elif (check_col==13):
						d = " %"
						if row_value[check_col] > 0:
							s = " + "					   
										
					if abs(row_value[check_col])==0 or abs(row_value[check_col-1])==0:
						htmlfile.write('<td style="background-color:#9FFF80">'+ s + column + d + '</td>') 
					elif (abs(row_value[check_col])/row_value[check_col-1])*100<10 or (row_value[check_col]<50 and check_col != 14):
						htmlfile.write('<td style="background-color:#9FFF80">'+ s + column + d + '</td>')
					elif (abs(row_value[check_col])/row_value[check_col-1])*100>10 and row_value[check_col]>0:
						htmlfile.write('<td style="background-color:#FF9999">'+ s + column + d + '</td>')
					else:
						htmlfile.write('<td style="background-color:#66FF33">'+ s + column + d + '</td>')
						
				elif (check_col==10) and num == 0: #errors for the current release				   
					if c_value>10:
						htmlfile.write('<td style="background-color:#FF9999">' + column + '</td>')
					else:
						htmlfile.write('<td>' + column + '</td>')
				elif (check_col==0):
					htmlfile.write('<td><a href="#'+column.replace('/','_')+str(num)+'">' + column +'</a></td>')
				else:	
					htmlfile.write('<td>' + column + '</td>')
				
				check_col+=1
			  
			htmlfile.write('</tr>')
		rownum += 1
  
	print "Created " + str(rownum) + " row table."
	htmlfile.write('</table>')
	
	htmlfile.write('<table>')
	htmlfile.write('"<thead><tr><div id="cpugraphs'+str(num)+'"><th colspan="2">CPU graphs:</th></div></tr></thead>') 
	htmlfile.write("<tr>")
	print "Opening monitoring data:"
	
	if os.path.isfile(jtl_files[num][1]) and os.stat(jtl_files[num][1]).st_size != 0:
		f = open(jtl_files[num][1],"r")
		lines = f.readlines()
		f.close()
		f = open(jtl_files[num][1],"w")
		for line in lines:
			if not ('start' in line):
				f.write(line)
		
		f.close()
		monitoring_data = pd.read_csv(jtl_files[num][1],index_col=1, sep=";")
		monitoring_data.columns = ['server_name','Memory_used','Memory_free','Memory_buff','Memory_cached','Net_recv','Net_send','Disk_read','Disk_write','System_la1','CPU_user','CPU_system','CPU_iowait']
		monitoring_data.index=pd.to_datetime(dateconv((monitoring_data.index.values)))
		num_lines = monitoring_data['server_name'].count()
		print "Lines in monitoring data"
		print num_lines
		
		byServer = monitoring_data.groupby('server_name') 
		mon[num] = byServer.aggregate({'CPU_user':np.mean})
		mon[num]['CPU_user'] = byServer.CPU_user.mean()
		mon[num]['CPU_system'] = byServer.CPU_system.mean()
		mon[num]['CPU_iowait'] = byServer.CPU_iowait.mean()	
		mon[num]['Summary'] = byServer.CPU_iowait.mean()+byServer.CPU_system.mean()+byServer.CPU_user.mean()
  
		summ = mon[num]['Summary']
		summ['Release'] = jtl_files[num][2]
		cpu_over_releases.append([summ])
		print "cpu_over_releases"
		print cpu_over_releases
		rownum_ = 0
		target_csv = report_dir +"pics/"+monitor_table+str(num)+'.csv'
		mon[num].to_csv(target_csv, sep=',')
		htmlfile.write('<div class="datagrid">')
		htmlfile.write('<table>')
		reader = csv.reader(open(target_csv))
		
		for row in reader: # Read a single row from the CSV file
	# write header row. assumes first row in csv contains header
		  if rownum_ == 0:
			  htmlfile.write('<thead><tr>') # write <tr> tag
			  for column in row:
				  htmlfile.write('<th>' + column + '</th>')
			  htmlfile.write('</tr></thead>')   
		  else:
			  htmlfile.write('<tr>')
			  check_col = 0	
			  for column in row: 
				  htmlfile.write('<td>' + column + '</td>')
						
				
			  htmlfile.write('</tr>')
		  rownum_ += 1
	
		print "Created " + str(rownum_) + " row table."
		htmlfile.write('</table>')
		
		server_names = {}
		server_names=monitoring_data['server_name'].unique()
		print "Server names: " + server_names
		for server in server_names:
			dfServer = monitoring_data[(monitoring_data.server_name == server)]
			cpu_user = dfServer.CPU_user
			cpu_system = dfServer.CPU_system
			cpu_iowait = dfServer.CPU_iowait
			
			
			#p95_rtot = df.groupby(pd.TimeGrouper(freq='10Min')).average.quantile(.95)
			ax = cpu_user.plot(marker='.',markersize=3,title='cpu load ' + str(server) ,label="cpu_user")
			ax = cpu_system.plot(marker='.',markersize=3,title='cpu load ' + str(server) ,label="cpu_system")
			ax = cpu_iowait.plot(marker='.',markersize=3,title='cpu load ' + str(server) ,label="cpu_iowait")
			ax.set_xlabel("Test time")
			ax.set_ylabel("cpu load (%)")
			ax.set_ylim(0,100)
			ax.legend()
			plt.tight_layout()
			destPng = report_dir +"pics/"+'cpu_user_'+str(num)  + ' ' +str(server)  + '.png'
			savefig(destPng)
			plt.cla()
			fig.clear()
			htmlfile.write("<td><img src='"+"pics/"+'cpu_user_'+str(num)  + ' ' +str(server)   + '.png' +"'></td>")
	else:
		print "Monitoring data is not exist"
	
	htmlfile.write("</tr>")
	htmlfile.write('<table>')	
	average_rtot = dataframes[num].groupby(pd.TimeGrouper(freq='10Min')).average.mean()
	median_rtot = dataframes[num].groupby(pd.TimeGrouper(freq='10Min')).average.median()
	ax = average_rtot.plot(marker='.',markersize=10,title='Response Times over Time',label="average")
	ax = median_rtot.plot(marker='.',markersize=10,title='Response Times over Time', label="median")
	ax.set_xlabel("Test time")
	ax.set_ylabel("Response time (ms)")
	ax.legend()
	plt.tight_layout()
	savefig(report_dir +"pics/"+'rtot_'+str(num) + '.png')
	plt.cla()
	overall_errors = dataframes[num][(dataframes[num].success == False)].groupby(pd.TimeGrouper(freq='10Min')).success.count()
	if not overall_errors.empty:
		ax = overall_errors.plot(title='Errors over Time', label="errors")
		ax.set_xlabel("Test time")
		ax.set_ylabel("Errors count")
		ax.legend()
		plt.tight_layout()
		savefig(report_dir +"pics/"+'errors_'+str(num) + '.png')
		plt.cla()
	font = {'family' : 'sans-serif',
	  #  'weight' : 'bold',
		'size'   : 8}
	response_codes = dataframes[num].groupby("responseCode").average.count()
	if not response_codes.empty:		
		response_codes.plot(kind='pie',autopct='%.2f', fontsize=7, figsize=(6, 6),label="response codes")
		ax.legend()
		plt.tight_layout()
		savefig(report_dir +"pics/"+'responsecodes_'+str(num) + '.png')
		plt.cla()
	fig = matplotlib.pyplot.gcf()
  
	font = {'family' : 'sans-serif',
	  #  'weight' : 'bold',
		'size'   : 6}
  
	matplotlib.rc('font', **font)
  
	agg[num][['average']].plot(kind='barh')
	print "hoiiii"
	print agg[num][['average']]
	plt.tight_layout()
	savefig(report_dir +"pics/"+'bar_small_'+str(num) + '.png')
	fig.set_size_inches(20.5, 10.5)
	savefig(report_dir +"pics/"+'bar_'+str(num) + '.png', dpi=300)
	plt.cla()
	fig.clear()
	htmlfile.write('<table>')
	htmlfile.write('<thead><tr><div id="overallgraphs'+str(num)+'"><th colspan="2">Overall test graphs:</th></div></tr></thead>') 
	htmlfile.write("<tr>")
	htmlfile.write("<td><img src='pics/rtot_"+str(num) + ".png'></td>")
	htmlfile.write("<td><img id='zoom_01' src='pics/bar_small_"+str(num) + ".png' data-zoom-image='pics/bar_"+str(num) + ".png'/></td>")
	htmlfile.write("</tr>")
	htmlfile.write("<tr>")
	htmlfile.write("<td><img src='pics/errors_"+str(num) + ".png'></td>")
	htmlfile.write("<td><img src='pics/responsecodes_"+str(num) + ".png'></td>")
	htmlfile.write("</tr>")
	htmlfile.write('<table>')
	dfURL={}
	uniqueURL = {}
	uniqueURL=dataframes[num]['URL'].unique()
	  
	print uniqueURL
	htmlfile.write('<table>')
	htmlfile.write('<thead><tr><div id="actiongraphs'+str(num)+'"><th colspan="2">Action graphs:</th></div></tr></thead>') 
	  
	url_count = 0
	for URL in uniqueURL:
		print "Generating graphs for %s" % URL
		if url_count%2 == 0:
			htmlfile.write('<tr class="alt">')
		else:
			htmlfile.write('<tr>')
		

		dfURL = dataframes[num][(dataframes[num].URL == URL)]
		average_rtot_url = dfURL.groupby(pd.TimeGrouper(freq='10Min')).average.mean()
		median_rtot_url = dfURL.groupby(pd.TimeGrouper(freq='10Min')).average.median()
		errors_url = dfURL[(dfURL.success == False)].groupby(pd.TimeGrouper(freq='10Min')).success.count()
		#p95_rtot = df.groupby(pd.TimeGrouper(freq='10Min')).average.quantile(.95)
		ax = average_rtot_url.plot(marker='.',markersize=10,title='Response Times over Time for ' + str(URL) ,label="average")
		ax = median_rtot_url.plot(marker='.',markersize=10,title='Response Times over Time for '  + str(URL) , label="median")
		ax.set_xlabel("Test time")
		ax.set_ylabel("Response time (ms)")
		ax.legend()
		plt.tight_layout()
		URL=URL.replace("?", "_").replace("/","_").replace('"',"_")
		destPng = report_dir +"pics/"+'rtot_'+str(num) + '_'+ URL + '.png'
		savefig(destPng)
		plt.cla()
		fig.clear()
		htmlfile.write("<td>"+'<h3 id="'+URL+str(num)+'">'+URL+'</h3>'+'<img src="'+"pics/"+'rtot_'+str(num) + '_'+ URL + '.png'+'"></td>')
		if len(errors_url)!=0:
			errors_url=errors_url.astype(float)
			ax = errors_url.plot(title='Errors s over Time for '  + str(URL) , label="errors")
			ax.set_xlabel("Test time")
			ax.set_ylabel("Response time (ms)")
			ax.legend()
			plt.tight_layout()
			URL=URL.replace("?", "_").replace("/","_")
			destPng = report_dir +"pics/"+ 'errors_'+ URL + '.png'
			savefig(destPng)
			htmlfile.write("<td><img src='"+"pics/"+ 'errors_'+ URL + '.png'+"'></td>")
			plt.cla()
			fig.clear()
		htmlfile.write("</tr>")
		url_count+=1
	  
	  
	htmlfile.write('</table>')
  
	htmlfile.write('</div>')
	htmlfile.write('</div>')
###############################################################################

htmlfile.write("""<div id="Overall">""")
htmlfile.write('<div class="datagrid">')
htmlfile.write('<table>') 
font = {'family' : 'sans-serif',
	  #  'weight' : 'bold',
		'size'   : 10} 
aopd = pd.DataFrame(rtot_over_releases, columns=['Release','Average', 'Median'])
aopd = aopd.set_index(['Release'])
aopd = aopd[::-1] #reverse
ax = aopd.plot(marker='.',markersize=10,title='Average Response Times through all releases',label="average")
ax.set_xlabel("Releases")
ax.set_ylabel("Response time (ms)")
ax.legend()
plt.tight_layout()
destPng = report_dir + "pics/rtot_over_releases.png"
savefig(destPng) 
htmlfile.write("<td>")
htmlfile.write(aopd.to_html(classes='table',escape=False,float_format=lambda x: '%10.1f' % x))
htmlfile.write("<img src='"+"pics/rtot_over_releases.png"+"'>")
htmlfile.write("</td>")
cpu_frames = []
for s in cpu_over_releases:
	print s
	x = pd.DataFrame(s)
	print x
	x = x.set_index(['Release'])
	cpu_frames.append(x)

result = pd.concat(cpu_frames)
result = result[::-1]
cpu_html_table = result.to_html(classes='table',escape=False,float_format=lambda x: '%10.1f' % x)
print cpu_html_table



ax = result.plot(kind='bar',title='Average CPU load on servers through all releases',label="average")
ax.set_xlabel("Releases")
ax.set_ylabel("CPU Load (%)")
ax.set_ylim(0,100)
ax.legend()  
plt.tight_layout()
destPng = report_dir + "pics/cpu_over_releases.png"
savefig(destPng) 

htmlfile.write("<td>")
htmlfile.write(cpu_html_table)
htmlfile.write("<img src='"+"pics/cpu_over_releases.png"+"'>")
htmlfile.write("</td>")
htmlfile.write('</div>')
htmlfile.write('</div>')
  
  
  
  
htmlfile.write(""" 
</div>
	""")
htmlfile.write("""
<script>
	$('#zoom_01').elevateZoom({
	zoomType: "inner",
cursor: "crosshair",
zoomWindowFadeIn: 500,
zoomWindowFadeOut: 750
   }); 
</script>
""")
htmlfile.write('</body>')
