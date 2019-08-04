from django.utils.encoding import smart_str, smart_unicode
from django.shortcuts import render

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import json
import csv
import xlwt
import datetime
import time
import UTF8Recoder

from .models import *;
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

def export_xls(request, season=0):
	if season == 0:
		season = datetime.date.today().year
		if datetime.date.today().month >= 10:
			season += 1

	season_start = datetime.date(int(season)-1, 10, 1)
	season_end = datetime.date(int(season), 9, 30)

	response = HttpResponse(content_type='application/ms-excel')
	response['Content-Disposition'] = 'attachment; filename="users.xls"'

	wb = xlwt.Workbook(encoding='utf-8')
	ws = wb.add_sheet('Users')

	# Sheet header, first row
	row_num = 0

	font_style = xlwt.XFStyle()
	font_style.font.bold = True

	columns = ['Datum', 'Beschreibung', 'Name', 'Projekt', 'Dauer', 'Bestaetigt bei']

	entry_list = None
	profile = request.user.userprofile;
#	if(profile.isleader):
	entry_list = Entry.objects.filter(date__gt=season_start, date__lt=season_end).order_by('-date')
#	else:
#		entry_list = Entry.objects.filter(date__gt=season_start, date__lt=season_end).filter(user=profile.user_id).order_by('-date')
	project_list = Project.objects.all().values_list('id', 'name', 'project')
	user_list = User.objects.all().values_list('id', 'first_name', 'last_name', 'username')
	context = {'season': season, 'user_profile': profile, 'entry_list': entry_list, 'project_list': project_list}

	projects = [None] * len(project_list)
	for project in project_list:
		projects[project[0]] = project[1]

	users = [None] * len(user_list)*5
	for user in user_list:
		users[user[0]] = user[1] + user[2]

	entry_list = entry_list.values_list('date', 'description', 'user', 'project', 'hours', 'leader')

	for col_num in range(len(columns)):
		ws.write(row_num, col_num, columns[col_num], font_style)

	# Sheet body, remaining rows
	font_style = xlwt.XFStyle()

	rows = entry_list
	for row in rows:
		row_num += 1
		for col_num in range(len(row)):
			entry = row
			leader = ''
			if (entry[5] != None):
				leader = users[entry[5]]
			my_entry = [entry[0].strftime("%d.%m.%Y"), entry[1], users[entry[2]], projects[entry[3]], str(entry[4]), leader]
			#ws.write(row_num, col_num, row[col_num], font_style)
			ws.write(row_num, col_num, my_entry[col_num], font_style)

	wb.save(response)
	return response

@login_required
def index(request, season=0):
	if season == 0:
		season = datetime.date.today().year
		if datetime.date.today().month >= 10:
			season += 1

	season_start = datetime.date(int(season)-1, 10, 1)
	season_end = datetime.date(int(season), 9, 30)

	response_data = {}
	response_data['id']= -1;
	if request.method == 'POST':
		if request.POST.get('entry_delete'):
			entryid = None
			e_id = -1
			entryid = request.POST.get('entry')
			if entryid is not None:
				entry = Entry.objects.get(id=entryid);
				if entry is not None and entry.leader is None:
					e_id = entry.id;
					profile = request.user.userprofile;
					if(entry.user_id == request.user.id):
						entry.delete()
			response_data['id'] = e_id;
			return HttpResponse(json.dumps(response_data),content_type="application/json")

		elif request.POST.get('entry_ok'):
			entryid = None
			e_id = -1
			entryid = request.POST.get('entry')
			profile = request.user.userprofile;
			if entryid is not None and profile.isleader:
				entry = Entry.objects.get(id=entryid);
				if entry is not None and entry.leader is None:
					e_id = entry.id;
					entry.leader = request.user;
					entry.save()
			response_data['id'] = e_id;
			return HttpResponse(json.dumps(response_data),content_type="application/json")

		elif request.POST.get('entry_add'):
			project = None
			try:
				project = Project.objects.get(name=request.POST.get('projekt_name'))
			except:
				pass
			if project is None:
				project, created = Project.objects.get_or_create(name='Sonstiges');
				if created:
					project.save()

			description = request.POST.get('beschreibung')
			dauer = request.POST.get('dauer')
			datetext = request.POST.get('datetext')
			if(description is None or dauer is None or datetext is None):
				response_data['text'] = "Eintrag unvollstaendig!";
				return HttpResponse(json.dumps(response_data),content_type="application/json")
			if(float(dauer) <= 0.0):
				response_data['text'] = "Geht nich";
				return HttpResponse(json.dumps(response_data),content_type="application/json")
			if ((float(dauer) % 0.5) != 0.0):
				response_data['text'] = "so gehts nich";
				return HttpResponse(json.dumps(response_data),content_type="application/json")
			if(datetime.datetime.strptime(datetext, "%Y-%m-%d") > datetime.datetime.now()):
				response_data['text'] = "Eintrag liegt in der Zukunft!";
				return HttpResponse(json.dumps(response_data),content_type="application/json")

			if(datetime.datetime.strptime(datetext, "%Y-%m-%d") < datetime.datetime.now()- datetime.timedelta(days=12)):
				response_data['text'] = "Zeit fuer Eintragung verstrichen. Fuer Sondereintragung an Admin wenden!";
				return HttpResponse(json.dumps(response_data),content_type="application/json")
		
			entry = Entry(user=request.user, project=project, description=description, hours=dauer, date=datetext)
			entry.save()

			response_data['id'] = entry.id;
			return HttpResponse(json.dumps(response_data),content_type="application/json")
	
	entry_list = None
	profile = request.user.userprofile;
	entry_list = Entry.objects.filter(date__gt=season_start, date__lt=season_end).order_by('date')
	user_array = []
	for entry in User.objects.all():
		user_array.append(int(entry.id))
		user_array.append(smart_str(entry.last_name, encoding='iso-8859-1', errors='ignore'))
	entry_array = []
	for entry in entry_list:
		entry_array.append(int(entry.id))
		entry_array.append(int(entry.user_id))
		entry_array.append(entry.date.strftime("%d.%m.%Y"))
		entry_array.append(smart_str(entry.description, encoding='iso-8859-1', errors='ignore'))
		entry_array.append(int(entry.project_id))
		entry_array.append(float(entry.hours))
		entry_array.append(str(entry.leader_id))
	project_list = Project.objects.all()
	context = {'season': season, 'user_profile': profile, 'entry_array': entry_array, 'project_list': project_list, 'user_array': user_array}
	return render(request, 'index.html', context)

@login_required
def users(request, season=0):
	if season == 0:
		season = datetime.date.today().year
		if datetime.date.today().month >= 10:
			season += 1

	season_start = datetime.date(int(season)-1, 10, 1)
	season_end = datetime.date(int(season), 9, 30)

	profile = request.user.userprofile;
	if request.method == 'POST':
		if(not profile.isleader):
			return HttpResponse(json.dumps({}),content_type="application/json")
		e_id = -1
		userid = request.POST.get('userid')
		if userid is not None:
			user = User.objects.get(id=userid);
			if user is not None:
				user_profile = user.userprofile;
				if(not user_profile.isleader):
					user_profile.isleader = True;
				else:
					user_profile.isleader = False;
				user_profile.save()
				e_id = user.id;
			
		response_data = {}
		response_data['id'] = e_id;
		return HttpResponse(json.dumps(response_data),content_type="application/json")

	entry_list = Entry.objects.filter(date__gt=season_start, date__lt=season_end).order_by('-date')
	entry_array = []
	for entry in entry_list:
		entry_array.append(int(entry.user_id))
		entry_array.append(float(entry.hours))
		entry_array.append(entry.date.strftime("%Y-%m-%d"))
		entry_array.append(int(entry.leader is None))

	profile_list = UserProfile.objects.exclude(user=User.objects.get(username="admin")).filter(user__in=entry_list.values_list('user', flat=True))

	context = {'season': season, 'entry_array': entry_array, 'profile_list': profile_list}
	return render(request, 'users.html', context)

@login_required
def projects(request, season=0):
	if season == 0:
		season = datetime.date.today().year
		if datetime.date.today().month >= 10:
			season += 1

	season_start = datetime.date(int(season)-1, 10, 1)
	season_end = datetime.date(int(season), 9, 30)

	profile = request.user.userprofile;
	if request.method == 'POST':
		response_data = {}
		e_id = -1
		if(not profile.isleader):
			return index(request);
		if request.POST.get('project_add'):
			project = None
			project_name = request.POST.get('name')
			if project_name is not None:
				project, created = Project.objects.get_or_create(name=project_name);
				e_id = project.id;
				if created:
					project.save()
		elif request.POST.get('project_delete'):
			project = None
			project_id = request.POST.get('project')
			if project_id is not None:
				project = Project.objects.get(id=project_id);
				if project is not None:
					e_id = project.id;
					project.delete()

		elif request.POST.get('rename'):
			project = None
			project_name = request.POST.get('project_name')
			project_new_name = request.POST.get('new_project_name')
			if project_name is not None and project_new_name is not None:
				project = Project.objects.get(name);
				if project is not None :
					project.name = project_new_name
					e_id = project.id;
					project.save()

		response_data['id'] = e_id;
		return HttpResponse(json.dumps(response_data),content_type="application/json")

	entry_list = Entry.objects.filter(date__gt=season_start, date__lt=season_end).order_by('-date')
	entry_array = []
	for entry in entry_list:
		entry_array.append(int(entry.project_id))
		entry_array.append(float(entry.hours))
		entry_array.append(entry.date.strftime("%Y-%m-%d"))
	project_list = Project.objects.all()
	entry_list = None
	context = {'season': season, 'entry_array': entry_array, 'project_list': project_list}
	return render(request, 'projects.html', context)
