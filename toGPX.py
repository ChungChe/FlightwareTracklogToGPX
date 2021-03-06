# Flightaware tracklog to gpx
# 1. Use wget to get tracklog
# e.g.
#	wget http://flightaware.com/live/flight/EVA7/history/20160508/0800Z/KSFO/RCTP/tracklog
# To generate gpx file
# set use_gpx = True to generate gpx file
# e.g 
#	python toGPX.py tracklog > output.gpx 
# if use_gpx = False
# e.g 
#	python toGPX.py tracklog > output.html

import sys
from bs4 import BeautifulSoup
import codecs

step = 10000.0

def parse_gps_position(sp, name):
	data = []
	result1 = sp.find_all(lambda tag: tag.name == 'tr' and tag.get('class') ==  [name])
	if result1 == None:
		f.close()
		return	
	for ele in result1:
		tr_ary = ele.find_all('td')
		count = 0
		for td_ele in tr_ary:
			count += 1
			if count <= 3:
				data.append(td_ele.contents[0])
	return data

def plot2gpx(x, y):
	print('      <trkpt lat="{0}" lon="{1}"></trkpt>'.format(float(y/step), float(x/step)))

def plot2svg(x, y, size, color):
	print('<g><circle cx="{0}" cy="{1}" r="{2}" stroke="black" fill={3}></circle></g>'.format(x, y, size, color))

# x0 y0 x1 y1 should be integer
def bresenham_line(x0, y0, x1, y1, flag):
	#print('    34 draw ({0}, {1}) to ({2}, {3})'.format(x0, y0, x1, y1))
	#if flag == False:
	#	if x0 * x1 >= 0:
	#		print('<line x1="{0}" y1="{1}" x2="{2}" y2="{3}" style="stroke:rgb(0,0,255);stroke-width:1000" />'.format(x0, y0, x1, y1))	

	steep = abs(y1- y0) > abs(x1 -x0)
	if steep:
		# swap x0 y0
		x0, y0 = y0, x0
		# swap x1 y1
		x1, y1 = y1, x1
	if x0 > x1:
		# swap x0 x1
		x0, x1 = x1, x0
		# swap y0 y1
		y0, y1 = y1, y0
	deltax = x1 - x0
	deltay = abs(y1 - y0)
	error = deltax / 2
	y = y0
	ystep = -1
	if y0 < y1:
		ystep = 1
	#print('x0={0}, x1={1}'.format(x0, x1)) 
	for x in range(x0, x1):
		if steep:
			#print('x={0}, y={1}'.format(y, x)) 
			if flag:
				plot2gpx(y, x)
			else:
				plot2svg(y, x, 1000, "green")
		else:
			#print('x={0}, y={1}'.format(x, y)) 
			if flag:
				plot2gpx(x, y)
			else:
				plot2svg(x, y, 1000, "green")
		error -= deltay
		if error < 0:
			y += ystep
			error += deltax

def gen_gpx(ary, enable_inter):
	print("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
	print("<gpx>")
	print("  <trk><name>GG</name><src>tracelog to gps</src>")
	print("    <trkseg>")
	for i in range(0, len(ary) - 1):
		y0 = int(float(ary[i][1]) * step)
		x0 = int(float(ary[i][2]) * step)
		y1 = int(float(ary[i+1][1]) * step)
		x1 = int(float(ary[i+1][2]) * step)
	 	gg = int(180.0 * step)
		if (enable_inter):
			if x0 * x1 < 0 and x0 != x1:
				y2 = ((x1 - 180) * y0 - (x0 + 180) * y1) / (x1 - x0 - 360)
				#print('      y2 = {0}'.format(y2))
				if x0 < 0:
					#print('87 draw ({0}, {1}) to ({2}, {3})'.format(x0, y0, x1, y1)) 
					# (x1, y1) <-- (180, y2) <-- (-x0, y0)
					bresenham_line(int(-179.9999 * step), y2, x0, y0, True)
					bresenham_line(x1, y1, gg, y2, True)
				else:
					#print('92 draw ({0}, {1}) to ({2}, {3})'.format(x0, y0, x1, y1)) 
					# (x0, y0) --> (180, y2) --> (-x1, y1)
					bresenham_line(x0, y0, gg, y2, True)
					bresenham_line(int(-179.9999 * step), y2, x1, y1, True)
			else:
				#print('97 draw ({0}, {1}) to ({2}, {3})'.format(x0, y0, x1, y1)) 
				bresenham_line(x0, y0, x1, y1, True)
		else:
			plot2gpx(x0, y0)
	print("    </trkseg>")
	print("  </trk>")
	print("</gpx>")

'''
Try to generate the string like this:

var data = [
  {x:10,y:10},
  {x:50,y:100},
  {x:60,y:50},
  {x:100,y:30}
];

'''
def get_svg_data(ary, minY, maxY):
	head = 'var data = ['
	tail = '];'
	body = ''
	magic = (maxY + minY) / step
	for i in range(0, len(ary)):
		y0 = magic - float(ary[i][1])
		x0 = float(ary[i][2])
		if x0 < 0:
			new_x0 = x0 + 180.0
		else:
			new_x0 = x0 - 180.0
		if i == len(ary) - 1:
			body += '{{x: {0}, y: {1}}}'.format(new_x0, y0)
		else:
			body += '{{x: {0}, y: {1}}},'.format(new_x0, y0)
	return head + body + tail

def normailize(x):
	if x <= 0:
		new_x = x + 1800000
	else:
		new_x = x - 1800000
	return new_x

def gen_html(ary, minX, minY, maxX, maxY, enable_inter):
	# Hack time!	
	html_header = """
<!DOCTYPE html>
<html>
<meta charset="utf-8">
<title>Zoom + Pan</title>
<style>

.overlay {
  fill: none;
  pointer-events: all;
}

</style>
<body>
<script src="http://d3js.org/d3.v3.min.js"></script>
<script>

var width = 1280,
    height = 300;

	""" + get_svg_data(ary, minY, maxY) + """

var svg = d3.select('body')
	.append('svg')
    .attr("width", width)
    .attr("height", height)
	.attr("viewBox", 
	""" + '"{0} {1} {2} {3}"'.format(minX, minY, maxX-minX, maxY-minY) + """)

var line = d3.svg.line()
	.x(function(d) {
		return d.x * 10000.0;
	})
	.y(function(d) {
		return d.y * 10000.0;
	});

var path = svg.append('path')
	.attr({
		'd': line(data),
		'stroke': '#F00',
		'stroke-width': '1000px',
		'fill': 'none'
	});

</script>	
	"""
	print(html_header)
	print('<svg width="1280" height="300" viewbox="{0} {1} {2} {3}">'.format(str(minX), str(minY), str(maxX-minX), str(maxY-minY)))
	print('<line x1="{0}" y1="{1}" x2="{2}" y2="{3}" style="stroke:rgb(0,255,0);stroke-width:2000" />'.format(0, minY, 0, maxY))	
	magic = maxY + minY
	for i in range(0, len(ary) - 1):
		y0 = magic - int(float(ary[i][1]) * step)
		x0 = int(float(ary[i][2]) * step)
		y1 = magic - int(float(ary[i+1][1]) * step)
		x1 = int(float(ary[i+1][2]) * step)
		#print('x0: {0}, x1: {1}'.format(x0, x1))
		new_x0 = normailize(x0)
		new_x1 = normailize(x1)	
		#print('new_x0: {0}, new_x1: {1}'.format(new_x0, new_x1))
	 	gg = int(normailize(180.0 * step))
		
		if enable_inter:
			if new_x0 * new_x1 < 0 and new_x0 != new_x1:
				y2 = ((x1 - 180) * y0 - (x0 + 180) * y1) / (x1 - x0 - 360)
				if x0 < 0:
					#print('216 draw ({0}, {1}) to ({2}, {3})'.format(new_x0, y0, new_x1, y1)) 
					# (x1, y1) <-- (180, y2) <-- (-x0, y0)
					bresenham_line(int(normailize(-179.9999 * step)), y2, new_x0, y0, False)
					bresenham_line(new_x1, y1, gg, y2, True)
				else:
					#print('221 draw ({0}, {1}) to ({2}, {3})'.format(new_x0, y0, new_x1, y1)) 
					# (x0, y0) --> (180, y2) --> (-x1, y1)
					bresenham_line(new_x0, y0, gg, y2, True)
					bresenham_line(int(normailize(-179.9999 * step)), y2, new_x1, y1, False)
			else:
				#print('226 draw ({0}, {1}) to ({2}, {3})'.format(new_x0, y0, new_x1, y1)) 
				bresenham_line(new_x0, y0, new_x1, y1, False)

		plot2svg(new_x0, y0, 2000, "red")
				
	new_y1 = magic - int(float(ary[len(ary)-1][1]) * step)
	new_x1 = int(float(ary[len(ary)-1][2]) * step)
	plot2svg(new_x1, new_y1, 2000, "red")
	print("</svg></body></html>")

def main(filename):
	use_gpx = True 

	f = codecs.open(filename, "r", "utf-8")
	if f == None:
		exit(0)
	content = f.read()
	soup = BeautifulSoup(content)

	data1 = parse_gps_position(soup, 'smallrow1')
	data2 = parse_gps_position(soup, 'smallrow2')

	data = data1 + data2
	ary = []
	minX = 99999999
	minY = 99999999
	maxX = -99999999
	maxY = -99999999

	for i in range(0, len(data), 3):
		tup = (str(data[i]), str(data[i+1]), str(data[i+2]))
		y = int(float(data[i+1]) * step)
		x = int(float(data[i+2]) * step)
	    
		new_x = normailize(x)	

		if new_x < minX:
			minX = new_x
		if y < minY:
			minY = y
		if new_x > maxX:
			maxX = new_x
		if y > maxY:
			maxY = y
		ary.append(tup)

	ary.sort()
	enable_inter = True
	if use_gpx:
		gen_gpx(ary, enable_inter)
	else:
		gen_html(ary, minX, minY, maxX, maxY, enable_inter)

	f.close()

main(sys.argv[1])
