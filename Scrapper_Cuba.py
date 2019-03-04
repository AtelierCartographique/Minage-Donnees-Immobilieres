from html.parser import HTMLParser 
from bs4 import BeautifulSoup
import re
import os
from urllib.request import Request, urlopen
from urllib import parse
import datetime
import csv
from tqdm import tqdm
import os
import zipfile
import dateparser as dateparser
from dateutil.relativedelta import relativedelta
import shapefile # PyShp
from pyproj import Proj, transform
from shapely.geometry import Polygon,Point
import chardet
import xlwt

BASE_DATE = datetime.datetime(2018, 1, 1)

def computeAvgByYearAndConsejoPop(fileName,L):
	
	try: 
		if 'Average' in L[0][16]:
			pass
	except:
		L[0].append('Average by year of publishing and consejoPop')
		L[0].append('Average by year of publishing and municipo')
	
	for l1 in L:
		if 'Published' not in l1[13] and (l1[13] != '?' and l1[14] != '?'):
			lieu, date = l1[14],l1[13].split('-')[0]
			prix = []
			for l2 in L:
				if l2[14] == lieu and l2[13].split('-')[0] == date and l2[1] != 'Price':
					prix.append(float(l2[1]))
			if len(prix) != 0:
				try:
					l1[16] = (sum(prix)/len(prix))
				except:
					l1.append(sum(prix)/len(prix))

	with open('Databases/' + fileName + '_avg.csv','w') as f:
		writer = csv.writer(f)
		writer.writerows(L)
	
	book = xlwt.Workbook()
	sh = book.add_sheet('data')
		
	for i,c in enumerate(L):
		for j,r in enumerate(c):
			sh.write(i,j,r)
#			print(i,j,r)
	book.save('Databases/' + fileName + '_avg.xls')
	

def computeAvgByYearAndMunicipio(fileName,L):
	
	try:
		if 'Average' in L[0][17]:
			pass
	except:
		L[0].append('Average by year of publishing and consejoPop')
		L[0].append('Average by year of publishing and municipo')
	
	for l1 in L:
		if 'Published' not in l1[13] and (l1[13] != '?' and l1[15] != '?'):
			lieu, date = l1[15],l1[13].split('-')[0]
			prix = []
			for l2 in L:
				if l2[15] == lieu and l2[13].split('-')[0] == date and l2[1] != 'Price':
					prix.append(float(l2[1]))
			if len(prix) != 0:
				try:
					l1[17] = (sum(prix)/len(prix))
				except:
					l1.append(sum(prix)/len(prix))

	with open('Databases/' + fileName + '_avg.csv','w') as f:
		writer = csv.writer(f)
		writer.writerows(L)


def toGeojson(t):
	
	myshpPop = open("7ConsPop/7ConsPop.shp", "rb")
	mydbfPop = open("7ConsPop/7ConsPop.dbf", "rb")
	rPop = shapefile.Reader(shp=myshpPop, dbf=mydbfPop)
	shapesPop = rPop.shapes()
	fieldsPop = rPop.fields
	recordsPop = rPop.records
	shapeRecsPop = rPop.iterShapeRecords()
	inProj = Proj(init='epsg:3795')
	outProj = Proj(init='epsg:4326')
		
	listPx1,listPx2 = [],[]

	geoJson = ' {"type": "FeatureCollection","features": ['
	for w in t:
		if 'Type' not in w[0]:
			lon1 = w[9]
			lat1 = w[8]
			px1 =  w[1]
			px2 =  w[2]
			geoJson += '{ "type": "Feature","geometry": {"type": "Point", "coordinates": [' + str(lon1) + ',' + str(lat1) + ']},"properties": {"Prix":' + str(px1) + ',"nbrPiece":' + str(px2) + '}},'
	
	c = 0
	for r in shapeRecsPop:
		geoJson += '{ "type": "Feature","geometry": {"type": "Polygon", "coordinates": [['
		c = 0
		for p in list(Polygon(r.shape.points).exterior.coords):
			c += 1
			if c > 10:
				c = 0
				break
			lng,lat = transform(inProj,outProj,p[1],p[0])
			geoJson += '[' + str(lng) + ',' + str(lat) + '],'
		geoJson = geoJson[:-1]
		geoJson += "]]}},"
		
			
	geoJson = geoJson[:-1] + "]}"
	return geoJson


def whichPop(lat,lng):
	
	myshpPop = open("7ConsPop/7ConsPop.shp", "rb")
	mydbfPop = open("7ConsPop/7ConsPop.dbf", "rb")
	rPop = shapefile.Reader(shp=myshpPop, dbf=mydbfPop)
	shapesPop = rPop.shapes()
	fieldsPop = rPop.fields
	recordsPop = rPop.records
	shapeRecsPop = rPop.iterShapeRecords()
	inProj = Proj(init='epsg:4326')
	outProj = Proj(init='epsg:3795')
	
	municipio, consejoPop = "?","?"
	for shapeRec in shapeRecsPop:
		pop = Polygon(shapeRec.shape.points)
		x1,y1 = transform(inProj,outProj,lng,lat)
		point = Point((x1,y1))
		if pop.contains(point):
			municipio, consejoPop = shapeRec.record[1],shapeRec.record[2]
	return municipio, consejoPop

def get_relative_date(date_string):
	parsed_date = dateparser.parse(date_string, settings={"RELATIVE_BASE": BASE_DATE})
	return relativedelta(parsed_date, BASE_DATE)

#os.environ["PATH"] += os.pathsep + r'/Volumes/Seagate Backup Plus Drive/Departement_de_geo/Violaine/Python/';

def zipdir(path, ziph):
	# ziph is zipfile handle
	for root, dirs, files in os.walk(path):
		for file in files:
			ziph.write(os.path.join(root, file))

def column(matrix, i):
	return [row[i] for row in matrix]

class LinkParser(HTMLParser):

	def handle_starttag(self, tag, attrs):
		if tag == 'a':
			for (key, value) in attrs:
				if key == 'href':
					newUrl = parse.urljoin(self.baseUrl, value)
					self.links = self.links + [newUrl]
	def getLinks(self, url):
		self.links = []
		self.baseUrl = url
		
		timeOut = False
		
		req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
#		req = Request(url, headers={'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A'})
		response = urlopen(req,timeout=30)#.read()
		htmlBytes = response.read()

		try:
			try:
				htmlString = htmlBytes.decode("utf-8")
			except:
				htmlString = htmlBytes.decode('latin-1')
			self.feed(htmlString)
			return htmlString, self.links
		except:
			return "", []

def spiderDestras(url,p):
	
	print('-',url + str(p))
		
	data = ""
	links = []
	c = 0
	parser = LinkParser()
	while data == "" and c < 10:
		c += 1
		data, links = parser.getLinks(url + str(p))

	ads = []
	for i,l in enumerate(links):
		if len(l.split('/')) == 7:
			if any(char.isdigit() for char in l.split('/')[6]):
				link = l.split('/')[0] + '/' + l.split('/')[1] + '/' + l.split('/')[2] + '/' + l.split('/')[5] + '/' + l.split('/')[6]
				ads.append(link)
	
	c = 0
	for l in ads:
		c += 1
		if l not in column(immobilier_cuba_all, 11):
			data = ""
			links = []
			cc = 0
			while data == "" and cc < 10:
				cc += 1
				try:
					data, links = parser.getLinks(l)
				except:
					data = ""
					links = []
		else:
			data = ""
			links = []
			print(p,c,"Existe déjà dans la BD...",l)
		
		if data != "" and 'latitude' in data:
			soup = BeautifulSoup(data, 'lxml')
			
			lat,lng,typeOfProperty,rooms,bedrooms,bathrooms,surface,year,price,address,info,piso = "?","?","?","?","?","?","?","?","?","?","?","?"
			
			lat = float(str(soup.find("meta",  property="og:latitude")).replace('<meta content="','').replace('" property="og:latitude"/>',''))
			lng = float(str(soup.find("meta",  property="og:longitude")).replace('<meta content="','').replace('" property="og:longitude"/>',''))
			
			results = [[re.sub('\s{2,}|\n+', '', i.text) for i in b.find_all('div')] for b in soup.find_all('div', {'class':'row'})]
			results2 = {}
			for r in results:
				if len(r) > 1:
					r[0] = r[0].replace(' ','-')
					if r[1] != '1+2+3+4+5+6+7+8+':
						results2[r[0].replace(' ','-')] = r[1]

			municipio, consejoPop = whichPop(lat,lng)

			try:
				typeOfProperty = results2['Type-of-property:']
			except:
				pass
			try:
				rooms = results2['Rooms:']
			except:
				pass
			try:
				bathrooms = results2['Bathrooms:']
			except:
				pass
			try:
				price = results2['Sale-price:'].replace('CUC','').replace(' ','')
			except:
				pass
			try:
				address = results2['Address:']
			except:
				pass
			try:
				info = str(soup.findAll("p", {"class": "descripcion"})[0]).replace('<p class="descripcion" itemprop="description">','').replace('</p>','').replace('<br/>',' ')
			except:
				pass
			try:
				year = results2['Year-of-construction:']
			except:
				pass
			try:
				surface = results2['Surface:'].replace('mts2','').replace(' ','')
			except:
				pass
			
			publishedWhen = results2['Published:']
			delta = get_relative_date(publishedWhen)
			y,m,d,h = abs(delta.years),abs(delta.months),abs(delta.days),abs(delta.hours)
			dd = y * 365 + m * 30.5 + d + h/24		
			DD = datetime.timedelta(days=dd)
			publishingDate = datetime.datetime.now() - DD
			publishingDate = publishingDate.strftime("%Y-%m-%d")
#			print(1,  publishedWhen,publishingDate)
			
			if float(price) > 1000.0 and lat != "?" and lng != "?" and municipio != '?' and consejoPop != '?':
				
				destrasdelafachada_all.append([typeOfProperty,float(price),rooms,bathrooms,info,surface,piso,year,lat,lng,address,l,now.strftime("%Y-%m-%d"),publishingDate,consejoPop,municipio])
				destrasdelafachada_today.append([typeOfProperty,float(price),rooms,bathrooms,info,surface,piso,year,lat,lng,address,l,now.strftime("%Y-%m-%d"),publishingDate,consejoPop,municipio])
				immobilier_cuba_all.append([typeOfProperty,float(price),rooms,bathrooms,info,surface,piso,year,lat,lng,address,l,now.strftime("%Y-%m-%d"),publishingDate,consejoPop,municipio])
				
				with open('Databases/DestrasDeLaFachada_all.csv','w',encoding='utf8') as f:
					writer = csv.writer(f) 
					writer.writerows(destrasdelafachada_all)
					
				with open('Databases/Immobilier_Cuba.csv','w',encoding='utf8') as f:
					writer = csv.writer(f) 
					writer.writerows(immobilier_cuba_all)
				
				computeAvgByYearAndConsejoPop('Immobilier_Cuba',immobilier_cuba_all)
				computeAvgByYearAndMunicipio('Immobilier_Cuba',immobilier_cuba_all)
				
				 
				with open('Databases/DestrasDeLaFachada_' + now.strftime("%Y-%m-%d_%H-%M") + '.csv','w',encoding='utf8') as f:
					writer = csv.writer(f) 
					writer.writerows(destrasdelafachada_today)
					
				print(p,c,'Ajouté')
				
				with open('/Volumes/Seagate Backup Plus Drive/Departement_de_geo/Mamp/htdocs/violaine/immoCuba/immoCuba.geojson','w') as f:
					f.write(toGeojson(immobilier_cuba_all))
				
			else:
				print(p,c,"Existe déjà dans la BD",l)
			

def spiderEspacio(url,p):
	
	print(url + str(p))
	
	data = ""
	c = 0
	parser = LinkParser()
	while data == "":
		c += 1
		print("(Essai",c,")")
		data, links = parser.getLinks(url + str(p))
	ads = []
	
	soup = BeautifulSoup(data, 'lxml')
	for a in soup.find_all("a", {"class":"room-link"}):
		ads.append(str(a).replace('<a class="room-link" href="','').replace('"></a>',''))

	c = 0
	for l in ads: 
		print(l)
		c += 1
		if l not in column(immobilier_cuba_all, 11):
			data = ""
			cc = 0
			while data == "" or cc > 10:
				cc += 1
				data, links = parser.getLinks(l)
		else:
			data = ""
			print(p,c,"Existe déjà dans la BD...",l)
			
		if data != "":
			soup = BeautifulSoup(data, 'lxml')

			lat,lng,typeOfProperty,rooms,bedrooms,bathrooms,surface,year,price,address,info,piso = "?","?","?","?","?","?","?","?","?","?","?","?"

			address1 = str(soup).split('"address":"')[1].split('","address2":')[0] 
			address2 = str(soup).split('"address":"')[1].split('","address2":')[1].split(',"zipcode":')[0].replace('"','')
			address3 = str(soup).split('"address":"')[1].split('","address2":')[1].split(',"zipcode":')[1].split(',"furnished":')[0].replace('"','')
			address = address1 + ", " + address2 + ", " + address3
			
			for sc in soup.find_all('span', {'class' : 'price'}):
				if 'CUC' in str(sc):
					price = [int(s) for s in str(sc).replace('>',' ').replace(',','').split() if s.isdigit()][0]
						
			info = str(soup.find_all('p', {'class' : 'des'})[0]).replace('<p class="des">','').replace('</p>','').replace('<br/>','').replace('	','')
			
			for sc in soup.find_all('span'):
				if 'Cuartos:' in str(sc):
					rooms = str(sc).replace('<span>Cuartos: ','').replace('</span>','')

			pattern = re.compile("var RANDOM_LOCATION = .*;")
			var1 = pattern.findall(soup.text)[0].replace('var RANDOM_LOCATION = {','').replace('};','').split(',')
			
			pattern = re.compile("var PROPERTY = .*;")
			var2 = pattern.findall(soup.text)[0].replace('var PROPERTY = {','').replace('};','').split(',')
			
			results2 = {}
			for v in var1:
				if len(v.split(':')) > 1:
					results2[v.split(':')[0].replace('"','')] = v.split(':')[1].replace('"','')
			for v in var2:
				if len(v.split(':')) > 1:
					results2[v.split(':')[0].replace('"','')] = v.split(':')[1].replace('"','')			
			
			lat = float(results2['latitude'])
			lng = float(results2['longitude'])
			piso = float(results2['floors'])
			surface = float(results2['area_build'])
			bedrooms = float(results2['bedrooms'])
			bathrooms = float(results2['bathrooms'])
			year = float(results2['year_built'])
			price = float(results2['price'])
			
			municipio, consejoPop = whichPop(lat,lng)
			publishedOn = '?'

			if float(price) > 1000.0 and lat != "?" and lng != "?" and municipio != '?' and consejoPop != '?':
				
				espacio_all.append([typeOfProperty,float(price),rooms,bathrooms,info,surface,piso,year,lat,lng,address,l,now.strftime("%Y-%m-%d"),publishedOn,consejoPop,municipio])
				espacio_today.append([typeOfProperty,float(price),rooms,bathrooms,info,surface,piso,year,lat,lng,address,l,now.strftime("%Y-%m-%d"),publishedOn,consejoPop,municipio])
				immobilier_cuba_all.append([typeOfProperty,float(price),rooms,bathrooms,info,surface,piso,year,lat,lng,address,l,now.strftime("%Y-%m-%d"),publishedOn,consejoPop,municipio])
				with open('Databases/Tout_Espacio.csv','w',encoding='utf8') as f:
					writer = csv.writer(f) 
					writer.writerows(espacio_all)
					
				with open('Databases/Immobilier_Cuba.csv','w',encoding='utf8') as f:
					writer = csv.writer(f) 
					writer.writerows(immobilier_cuba_all)
				
				with open('Databases/Espacio_' + now.strftime("%Y-%m-%d_%H-%M") + '.csv','w',encoding='utf8') as f:
					writer = csv.writer(f) 
					writer.writerows(espacio_today)
				print(p,c,'Ajouté')
				
				computeAvgByYearAndConsejoPop('Immobilier_Cuba',immobilier_cuba_all)
				computeAvgByYearAndMunicipio('Immobilier_Cuba',immobilier_cuba_all)
				
				
			else:
				print(p,c,"Existe déjà dans la BD, ou prix, lat ou lng inexistants",typeOfProperty,float(price),rooms,bathrooms,surface,piso,year,lat,lng,address)
				print()

now = datetime.datetime.now()
zipf = zipfile.ZipFile('BackupDB/backup_' + now.strftime("%Y-%m-%d_%H-%M") + '.zip', 'w', zipfile.ZIP_DEFLATED)
zipdir('Databases/', zipf)
zipf.close()

try:
	csvfile = open('Databases/Tout_DestrasDeLaFachada.csv', encoding='utf8')
	destrasdelafachada_all = csv.reader(csvfile, delimiter=',', quotechar='"')
	destrasdelafachada_all = list(destrasdelafachada_all)
except:
	destrasdelafachada_all = [["Type","Price","Cuartos","Banos","Info","Superficie","Piso","Year","Lat","Long","Address","Url","Scrapped on","Published on","consejoPop","municipio"]]

try:
	csvfile = open('Databases/Tout_Espacio.csv', encoding='utf8')
	espacio_all = csv.reader(csvfile, delimiter=',', quotechar='"')
	espacio_all = list(espacio_all)
except:
	espacio_all = [["Type","Price","Rooms","Bathrooms","Info","Area","Floor","Year","Lat","Long","Address","Url","Scrapped on","Published on","consejoPop","municipio"]]

try:
	csvfile = open('Databases/Immobilier_Cuba.csv', encoding='utf8')
	immobilier_cuba_all = csv.reader(csvfile, delimiter=',', quotechar='"')
	immobilier_cuba_all = list(immobilier_cuba_all)
except:
	immobilier_cuba_all = [["Type","Price","Rooms","Bathrooms","Info","Area","Floor","Year","Lat","Long","Address","Url","Scrapped on","Published on","consejoPop","municipio"]]


destrasdelafachada_today = [["Type","Price","Cuartos","Banos","Info","Superficie","Piso","Year","Lat" ,"Long","Address","Url","Scrapped on","Published on","consejoPop","municipio"]]
espacio_today = [["Type","Price","Rooms","Bathrooms","Info","Area","Floor","Year","Lat","Long","Address","Url","Scrapped on","Published on","consejoPop","municipio"]]

now = datetime.datetime.now()				

for i in range(0,1000):
	print('Page',i)
	
	for q in ["habana-vieja", "centro-habana" , "vedado" , "playa", "cerro", "diez-de-octubre"]:
		print('Quartier',q)
		spiderEspacio('http://www.espaciocuba.com/search/results/location/' + q + '/',i)
	
	spiderDestras('https://www.detrasdelafachada.com/list-homes-sale-cuba/la-habana/',i)
	
#	spiderCubaconstructions('http://havana-houses.com/index.php/es/inmobiliaria-cuba-propiedades/apartamentos-se-vende?start=',i)