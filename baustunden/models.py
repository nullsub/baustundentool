from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.db import connections

class UserProfile(models.Model):
	user = models.OneToOneField(User)
	isleader = models.BooleanField(default=False)
	entrydate = models.DateTimeField('date of entry', default=None, null=True)

class Project(models.Model):
	name = models.CharField(max_length=200)
	app_label = 'baustunden'

class Entry(models.Model):
	user = models.ForeignKey(User)
	leader = models.ForeignKey(User, related_name='leader', null=True)
	project = models.ForeignKey(Project, related_name='project')
	isrejected = models.BooleanField(default=False)
	description = models.CharField(max_length=200)
	date = models.DateTimeField('date published')

	#fur alrich max_digits=6
	hours = models.DecimalField(max_digits=6, decimal_places=1)

def create_user_profile(sender, instance, created, **kwargs):
	profile, created = UserProfile.objects.get_or_create(user=instance)

#for the calculation of the monthly average we need the entrydate of new members. The monthly average uses the interval starting with their entry.
#the date of entry is fetched from "vorstandstool". TODO: use some cleaner mechanism
	cursor = connections['akaflieg_vorstand'].cursor()
	cursor.execute('SELECT eingetreten FROM mitglied WHERE mitglied.email = "' + profile.user.email + '"');
	profile.entrydate = cursor.fetchone()[0];

	profile.save();

post_save.connect(create_user_profile, sender=User)
