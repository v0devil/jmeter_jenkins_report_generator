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
matplotlib.style.use('bmh')



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

def get_dir_size(path):
	total_size = 0
	for dirpath, dirnames, filenames in os.walk(path):
		for f in filenames:
			if not f=='checksum': 
				fp = os.path.join(dirpath, f)
				total_size += os.path.getsize(fp)
	return total_size


jtl_files = []
releases = []

builds_dir=sys.argv[1]
report_dir=sys.argv[2]


DATA_DIR = report_dir + "data/"
IMAGES_DIR = report_dir + "images/"
	
build_xml = ElementTree()
for root, dirs, files in os.walk(builds_dir):
	for file in files:
		if file.endswith(".jtl"):
			if os.stat(os.path.join(root, file)).st_size>0: 
				build_parameters = []
				displayName = "unknown"
				monitoring_data =  os.path.join(root.replace('JMeterCSV','').replace('performance-reports',''), "monitoring.data")  
				build_xml_path = os.path.join(root.replace('JMeterCSV','').replace('performance-reports',''), "build.xml")	   
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
				if "Performance_HTML_Report" not in os.path.join(root, file):									   
					jtl_files.append([os.path.join(root, file),monitoring_data,displayName, build_parameters,root])

			  
jtl_files = sorted(jtl_files, key=getIndex,reverse=True)

releases.sort();
dateconv = np.vectorize(datetime.datetime.fromtimestamp)
  

aggregate_table='aggregate_table' 
monitor_table='monitor_table'


if not os.path.exists(DATA_DIR):
	os.makedirs(DATA_DIR)
if not os.path.exists(IMAGES_DIR):
	os.makedirs(IMAGES_DIR)


report_html = report_dir + 'report.html' 

print "Try to copy resources dir to report directory: " + report_dir

fromDirectory = "/home/report_gen/resourses/"
toDirectory = report_dir

copy_tree(fromDirectory, toDirectory + "/resourses/")
  
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
	$( "#tabs" ).tabs().addClass('tabs-left');
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
print "Trying to open CSV-files"
  
build_roots = [jtl_files[i][4]  for i in xrange(0,len(jtl_files))]

#dataframe to compare with:
df_ = pd.read_csv(jtl_files[0][0],index_col=0)  
df_.columns = ['average', 'URL','responseCode','success','threadName','failureMessage','grpThreads','allThreads']
df_.index=pd.to_datetime(dateconv((df_.index.values/1000)))
df_=df_[~df_['URL'].str.contains('exclude_')]
		
for build_root in build_roots:
	print "Current build directory:" + build_root
	checksum = -1
	PARSED_DATA_ROOT = build_root + "/parsed_data/"
	if not os.path.exists(PARSED_DATA_ROOT):
		os.makedirs(PARSED_DATA_ROOT)
	
	if os.path.exists(PARSED_DATA_ROOT + 'checksum'):
		with open(PARSED_DATA_ROOT + 'checksum', 'r') as f:
			checksum = f.readline()
		
		
	
	target_csv = PARSED_DATA_ROOT+"aggregate_table.csv"
	print 'checksum:' +  str(checksum) + '; directory size: ' + str(get_dir_size(PARSED_DATA_ROOT))
	if int(checksum)!=int(get_dir_size(PARSED_DATA_ROOT)) or checksum == -1:
	#if True:
		print "Executing a new parse... "
		df = pd.read_csv(jtl_files[file_index][0],index_col=0)		   
		
		df.columns = ['average', 'URL','responseCode','success','threadName','failureMessage','grpThreads','allThreads']
			#convert timestamps to normal date/time
		df.index=pd.to_datetime(dateconv((df.index.values/1000)))
		df=df[~df['URL'].str.contains('exclude_')]	   
				
		
		num_lines = df['average'].count()
		print "Number of lines in file 1: %d." % num_lines
		
	
		try:
			byURL = df.groupby('URL') # group date by URLs  
			agg[file_index] = byURL.aggregate({'average':np.mean}).round(1)
			#if file_index != 0:
				#agg[file_index]['average-diff'] = df_.groupby('URL').average.mean().round(1)-df.groupby('URL').average.mean().round(1)
			agg[file_index]['median'] = byURL.average.median().round(1)
			#if file_index != 0:
				#agg[file_index]['median-diff'] = df_.groupby('URL').average.median().round(1)-df.groupby('URL').average.median().round(1)  
			agg[file_index]['75_percentile'] = byURL.average.quantile(.75).round(1)
			agg[file_index]['90_percentile'] = byURL.average.quantile(.90).round(1)
			agg[file_index]['99_percentile'] = byURL.average.quantile(.99).round(1)
			agg[file_index]['maximum'] = byURL.average.max().round(1)
			agg[file_index]['minimum'] = byURL.average.min().round(1)
			agg[file_index]['count'] = byURL.success.count().round(1)
			#if file_index != 0:
				#agg[file_index]['count-diff'] = df_.groupby('URL').success.count().round(1)-df.groupby('URL').success.count().round(1)
			agg[file_index]['%_errors'] = ((1-df[(df.success == True)].groupby('URL')['success'].count()/byURL['success'].count())*100).round(1)
			#if file_index != 0:
				#agg[file_index]['%_errors_diff'] = (((1-df_[(df_.success == True)].groupby('URL').success.count()/df_.groupby('URL').success.count())*100)-((1-df[(df.success == True)].groupby('URL').success.count()/df.groupby('URL').success.count())*100)).round(1)
			
			print "Trying to save aggregate table to CSV-file: %s." % target_csv
			agg[file_index].to_csv(target_csv, sep=',')	
		except ValueError,e:
			print "error",e

	
	
		df.groupby(pd.TimeGrouper(freq='10Min')).average.mean().to_csv(PARSED_DATA_ROOT + "average_10.csv", sep=',')
		df.groupby(pd.TimeGrouper(freq='10Min')).average.median().to_csv(PARSED_DATA_ROOT + "median_10.csv", sep=',')  
		df[(df.success == False)].groupby(pd.TimeGrouper(freq='10Min')).success.count().to_csv(PARSED_DATA_ROOT + "overall_errors_10.csv", sep=',')  
		df.groupby("responseCode").average.count().to_csv(PARSED_DATA_ROOT + "response_codes.csv", sep=',')  
		

		
		dfURL={}
		uniqueURL = {}
		uniqueURL = df['URL'].unique()
		for URL in uniqueURL:
			URLdist=URL.replace("?", "_").replace("/","_").replace('"',"_")		 
#			if not os.path.exists(PARSED_DATA_ROOT + "average_10_"+URLdist+'.csv') or not os.path.exists(PARSED_DATA_ROOT + "median_10_"+URLdist+'.csv')or not os.path.exists(PARSED_DATA_ROOT + "errors_10_"+URLdist+'.csv'):
			dfURL = df[(df.URL == URL)]
			dfURL.groupby(pd.TimeGrouper(freq='10Min')).average.mean().to_csv(PARSED_DATA_ROOT + "average_10_"+URLdist+'.csv', sep=',')
			dfURL.groupby(pd.TimeGrouper(freq='10Min')).average.median().to_csv(PARSED_DATA_ROOT + "median_10_"+URLdist+'.csv', sep=',')
			dfURL[(dfURL.success == False)].groupby(pd.TimeGrouper(freq='10Min')).success.count().to_csv(PARSED_DATA_ROOT + "errors_10_"+URLdist+'.csv', sep=',')
	
		with open(PARSED_DATA_ROOT + 'checksum', 'w') as f:
			f.write('%d' % get_dir_size(PARSED_DATA_ROOT))		
		
	else:
		print "Using the exist data"
		agg[file_index] = pd.read_csv(target_csv, index_col=False, header=0)
	
	
	
	rtot_over_releases.append([jtl_files[file_index][2],agg[file_index].average.mean(),agg[file_index].average.median()]) 
	file_index += 1
	

   
		

 
htmlfile.write("""<div id="tabs">
  <ul>""")
 
htmlfile.write("""<li><a href='#Overall' style="background-color:#DEB339">Overall</a></li>""")	  
   
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
	target_csv = DATA_DIR + "aggregate_table_" + str(num) + ".csv"
	
	df = agg[num]
	
	if num != 0:
		df['average-diff'] = agg[0]['average']-df['average']
	if num != 0:
		df['median-diff'] = agg[0]['median']-df['median']
	if num != 0:
		df['count-diff'] = agg[0]['count']-df['count']
	if num != 0:
		df['%_errors_diff'] = agg[0]['%_errors']-df['%_errors']	
	if num != 0:
		df = df[['URL','average','average-diff','median','median-diff','75_percentile','90_percentile','99_percentile','maximum','minimum','count','count-diff','%_errors','%_errors_diff']]		
	
	df.to_csv(target_csv, sep=',', index=False)
	print num

num = 0


for build_root in build_roots:
	uniqueURL = []
	PARSED_DATA_ROOT = build_root + "/parsed_data/"
	htmlfile.write("""<div id="tabs-""")
	htmlfile.write(str(num))
	htmlfile.write("""">""")
 
	htmlfile.write('<ul id="vert_menu"><li><a href="#cpugraphs'+str(num)+'" class="current">cpu graphs</a><a href="#overallgraphs'+str(num)+'" class="current">overall graphs</a><a href="#actiongraphs'+str(num)+'" class="current">action graphs</a></li></ul>');
	rownum = 0
	htmlfile.write('<div class="datagrid" >')
	htmlfile.write('<table id="Table'+ str(num) +'" class="tablesorter">')
	#target_csv = PARSED_DATA_ROOT + "aggregate_table.csv"
	target_csv = DATA_DIR + "aggregate_table_" + str(num) + ".csv"
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
						 
				elif (check_col==9) and num == 0: #errors for the current release				   
					if c_value>10:
						htmlfile.write('<td style="background-color:#FF9999">' + column + '</td>')
					else:
						htmlfile.write('<td>' + column + '</td>')
				elif (check_col==0):
					uniqueURL.append(column)
					htmlfile.write('<td><a href="#'+column.replace('/','_')+str(num)+'">' + column +'</a></td>')
				else:	
					htmlfile.write('<td>' + column + '</td>')
				 
				check_col+=1
			   
			htmlfile.write('</tr>')
		rownum += 1
   
	print "Created " + str(rownum) + " row table."
	htmlfile.write('</table>')
	 
	font = {'family' : 'sans-serif',
	  #  'weight' : 'bold',
		'size'   : 8}
   
	matplotlib.rc('font', **font)
	 
	 
	htmlfile.write('<table>')
	htmlfile.write('<thead><tr><div id="cpugraphs'+str(num)+'"><th colspan="2">CPU graphs:</th></div></tr></thead>') 
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
		target_csv = IMAGES_DIR+monitor_table+str(num)+'.csv'
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
			 
			fig = plt.figure()
			#p95_rtot = df.groupby(pd.TimeGrouper(freq='10Min')).average.quantile(.95)
			ax = cpu_user.plot(marker='.',markersize=3,title='cpu load ' + str(server) ,label="cpu_user")
			ax = cpu_system.plot(marker='.',markersize=3,title='cpu load ' + str(server) ,label="cpu_system")
			ax = cpu_iowait.plot(marker='.',markersize=3,title='cpu load ' + str(server) ,label="cpu_iowait")
			ax.set_xlabel("Test time")
			ax.set_ylabel("cpu load (%)")
			ax.set_ylim(0,100)
			ax.legend()
			plt.tight_layout()
			destPng = IMAGES_DIR+'cpu_user_'+str(num)  + ' ' +str(server)  + '.png'
			savefig(destPng)
			plt.cla()
			fig.clear()
			htmlfile.write("<td><img src='"+"images/"+'cpu_user_'+str(num)  + ' ' +str(server)   + '.png' +"'></td>")
	else:
		print "Monitoring data is not exist"
	 
	htmlfile.write("</tr>")
	htmlfile.write('<table>')
	 
	 
	average_rtot = pd.read_csv(PARSED_DATA_ROOT + "average_10.csv", index_col=0, header=0,sep=",",names=['time','average'], parse_dates=[0])
	median_rtot = pd.read_csv(PARSED_DATA_ROOT + "median_10.csv", index_col=0, header=0,sep=",",names=['time','median'],parse_dates=[0])
	overall_errors = pd.read_csv(PARSED_DATA_ROOT + "overall_errors_10.csv", index_col=0, header=0,sep=",",names=['time','errors'],parse_dates=[0])
	
	fig = plt.figure()
	ax = fig.add_subplot(1,1,1)
	ax.plot(average_rtot.index.values,average_rtot,marker='.',markersize=10,label="average")
	ax.plot(median_rtot.index.values,median_rtot,marker='.',markersize=10, label="median")
	ax.set_title('Response Times over Time')
	ax.set_xlabel("Test time")
	ax.set_ylabel("Response time (ms)")
	ax.legend()
	plt.tight_layout()
	savefig(IMAGES_DIR+'rtot_'+str(num) + '.png')  
	plt.cla()
	fig.clear()
 
	 
	 
	if not overall_errors.empty:
		fig = plt.figure()
		ax = fig.add_subplot(1,1,1)
		ax.plot(overall_errors,marker='.',markersize=10,label="errors")
		ax.set_xlabel("Test time")		
		ax.set_ylabel("Errors count")
		ax.set_title('Errors over Time')
		ax.legend()
		plt.tight_layout()
		savefig(IMAGES_DIR+'errors_'+str(num) + '.png')
		plt.cla()
		fig.clear()
  
  
	  
	#response_codes = dataframes[num].groupby("responseCode").average.count()
	response_codes = pd.read_csv(PARSED_DATA_ROOT + "response_codes.csv",sep=",",names=['code','%'],index_col=0)
	print response_codes
	if not response_codes.empty:		
		fig = plt.figure()
	   # ax.pie(response_codes,autopct='%.2f')
		response_codes.plot(kind='pie',subplots=True,autopct='%.2f', fontsize=8, figsize=(6, 6),label="response codes")
		ax.set_xlabel("code")
		ax.set_title('Response codes')
		ax.legend()
		plt.tight_layout()
		savefig(IMAGES_DIR+'responsecodes_'+str(num) + '.png')
		plt.cla()
		fig.clear()
   
  
	
	agg[num][['average']].plot(kind='barh')
	 
	fig = plt.figure()
	savefig(IMAGES_DIR+'bar_small_'+str(num) + '.png')
	fig.set_size_inches(20.5, 10.5)
	savefig(IMAGES_DIR+'bar_'+str(num) + '.png', dpi=300)
	plt.cla()
	fig.clear()
	  
	htmlfile.write('<table>')
	htmlfile.write('<thead><tr><div id="overallgraphs'+str(num)+'"><th colspan="2">Overall test graphs:</th></div></tr></thead>') 
	htmlfile.write("<tr>")
	htmlfile.write("<td><img src='images/rtot_"+str(num) + ".png'></td>")
	htmlfile.write("<td><img id='zoom_01' src='images/bar_small_"+str(num) + ".png' data-zoom-image='images/bar_"+str(num) + ".png'/></td>")
	htmlfile.write("</tr>")
	htmlfile.write("<tr>")
	htmlfile.write("<td><img src='images/errors_"+str(num) + ".png'></td>")
	htmlfile.write("<td><img src='images/responsecodes_"+str(num) + ".png'></td>")
	htmlfile.write("</tr>")
	htmlfile.write('<table>')
	 
	 
	dfURL={}

	
	
	   
	htmlfile.write('<table>')
	htmlfile.write('<thead><tr><div id="actiongraphs'+str(num)+'"><th colspan="2">Action graphs:</th></div></tr></thead>') 
	   
	url_count = 0
	for URL in uniqueURL:
		print uniqueURL
		errors_url = []
		average_rtot_url = []
		median_rtot_url = []
		print "Generating graphs for %s" % URL
		if url_count%2 == 0:
			htmlfile.write('<tr class="alt">')
		else:
			htmlfile.write('<tr>')
		URL=URL.replace("?", "_").replace("/","_").replace('"',"_")
		print "Opening CSV-file %s" % PARSED_DATA_ROOT  + "average_10_"+URL +'.csv'	
		average_rtot_url = pd.read_csv(PARSED_DATA_ROOT + "average_10_"+URL+'.csv', index_col=0,sep=",",parse_dates=[0],names=['time','avg'])
		median_rtot_url = pd.read_csv(PARSED_DATA_ROOT + "median_10_"+URL+'.csv', index_col=0,sep=",",parse_dates=[0],names=['time','med'])
		 
		try:	
			errors_url = pd.read_csv(PARSED_DATA_ROOT + "errors_10_"+URL+'.csv', index_col=0, header=0,sep=",",parse_dates=[0])
		except ValueError,e:
			print("errors_10_"+URL+'.csv' +' has a zero size')
			 
		#p95_rtot = df.groupby(pd.TimeGrouper(freq='10Min')).average.quantile(.95)
		fig = plt.figure()
		ax = fig.add_subplot(1,1,1)
		ax.clear()
		
		ax.plot(average_rtot_url.index.values,average_rtot_url,marker='.',markersize=10,label="average")
		ax.plot(median_rtot_url.index.values,median_rtot_url,marker='.',markersize=10, label="median")
		ax.set_title('Response Times over Time for ' + str(URL))
		ax.set_xlabel("Test time")
		ax.set_ylabel("Response time (ms)")
		ax.legend()
		plt.tight_layout()
		savefig(IMAGES_DIR+'rtot_'+str(num) + '_'+ URL + '.png')
		plt.cla() 
		fig.clear()
		htmlfile.write("<td>"+'<h3 id="'+URL+str(num)+'">'+URL+'</h3>'+'<img src="'+"images/"+'rtot_'+str(num) + '_'+ URL + '.png'+'"></td>')
		if len(errors_url)!=0:
			 
			print errors_url
			errors_url=errors_url.astype(float)
			fig = plt.figure()
			ax = errors_url.plot(title='Errors s over Time for '  + str(URL) , label="errors")
			ax.set_xlabel("Test time")
			ax.set_ylabel("Errors")
			ax.legend()
			plt.tight_layout()
			URL=URL.replace("?", "_").replace("/","_") 
			savefig(IMAGES_DIR+ 'errors_'+ URL + '.png')
			plt.cla() 
			fig.clear()
			htmlfile.write("<td><img src='"+"images/"+ 'errors_'+ URL + '.png'+"'></td>")
		htmlfile.write("</tr>")
		url_count+=1
	   
	   
	htmlfile.write('</table>')
   
	htmlfile.write('</div>')
	htmlfile.write('</div>')
	num = num + 1
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
destPng = report_dir + "images/rtot_over_releases.png"
savefig(destPng) 
htmlfile.write("<td>")
htmlfile.write('<div class="scrollit">')
 
htmlfile.write(aopd.to_html(classes='table',escape=False,float_format=lambda x: '%10.1f' % x))
htmlfile.write('</div>')
htmlfile.write("<img src='"+"images/rtot_over_releases.png"+"'>")
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
destPng = report_dir + "images/cpu_over_releases.png"
savefig(destPng) 
 
htmlfile.write("<td>")
htmlfile.write('<div class="scrollit">')
htmlfile.write(cpu_html_table)
htmlfile.write('</div>')
htmlfile.write("<img src='"+"images/cpu_over_releases.png"+"'>")
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
