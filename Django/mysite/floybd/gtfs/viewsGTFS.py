
from django.shortcuts import render
from ..forms import UploadFileForm
import os
import tarfile
import zipfile
import time
from ..utils import *

def uploadGTFS(request):
	if request.method == 'POST':
		title = request.POST['title']
		form = UploadFileForm(request.POST, request.FILES)
		if form.is_valid():
			millis = int(round(time.time() * 1000))
			form.title = title
			kmlPath = handle_uploaded_file(request.FILES['file'],form.title,millis)
			return render(request, 'floybd/gtfs/viewGTFS.html', {'form': form,'kml':kmlPath})
	else:
		form = UploadFileForm()
		return render(request, 'floybd/indexGTFS.html', {'form': form})


def handle_uploaded_file(f, title, millis):
	ip  = getIp()
	if not os.path.exists("static/upload/gtfs"):
		print("Creating upload/gtfs folder")
		os.makedirs("static/upload/gtfs")

	extension = get_extension(f)

	#if extension is not ["zip","tar","tgz"]:
	saveNormalFile(f, title, extension)
	#else:
	#	decompressFile(f, title, extension)

	# kmlwriter.py google_transit.zip googleTest.kml
	zipName = title+"."+extension
	kmlName = title+"_"+str(millis)+".kml"
	kmlPath = "http://"+ip+":8000/static/kmls/" + kmlName

	command = "python2 static/utils/gtfs/kmlwriter.py static/upload/gtfs/"+zipName+" static/kmls/"+kmlName
	os.system(command)

	return kmlPath



def get_extension(file):
	name, extension = os.path.splitext(file.name)
	return extension

def saveNormalFile(file, title, extension):
	with open('static/upload/gtfs/' + title + "." + extension, 'wb+') as destination:
		for chunk in file.chunks():
			destination.write(chunk)

def decompressFile(file, title, extension):
	if file.endswith('.zip'):
		opener, mode = zipfile.ZipFile, 'r'
	elif file.endswith('.tar.gz') or file.endswith('.tgz'):
		opener, mode = tarfile.open, 'r:gz'
	elif file.endswith('.tar.bz2') or file.endswith('.tbz'):
		opener, mode = tarfile.open, 'r:bz2'
	else:
		raise (ValueError, "Could not extract `%s` as no appropriate extractor is found" % file)

	cwd = os.getcwd()

	if not os.path.exists("static/upload/gtfs/"+title):
		os.makedirs("static/upload/gtfs/"+title)

	os.chdir("static/upload/gtfs/"+title)

	try:
		compressedFile = opener(file, mode)
		try:
			compressedFile.extractall()
		finally:
			compressedFile.close()
	finally:
		os.chdir(cwd)


def sendGTFSToLG(request):
	kmlPath = request.POST["kmlPath"]
	form = UploadFileForm()

	command = "echo '" + kmlPath + "' | sshpass -p lqgalaxy ssh lg@192.168.88.198 'cat - > /var/www/html/kmls.txt'"
	os.system(command)

	return render(request, 'floybd/gtfs/viewGTFS.html', {'form': form, 'kml': kmlPath})