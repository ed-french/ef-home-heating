import webapp2,json,logging

from settings import Settings
from datetime import datetime
from google.appengine.api import users
import os

import jinja2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

"""
    Simple Programmable thermostat server-side application

    https://github.com/ed-french/ef-home-heating

    Provides GUI to modify the program easily

    The main page is provided from a static file

    The profiles are retreived and ammended via json endpoints:

    /bothprofilesjson retreives the temperature profiles and any other settings

    /getcurrenttemp retreives the required temperature right now

    /setslider?profile=weekdays&hour=12&temp=17.5 changes the stored setting




    To launch on dev server:
        from application directory:
            dev_appserver.py app.yaml
            
    To deploy to appengine:
        from application directory:
            gcloud app deploy
            
            

"""
    
class TempProfiles:
    """
        An instance contains the current temperature profiles,
        keeps these up-to-date with changes
        and returns interpolated temperatures

        Usage:

            tp=TempProfiles()  - Initialisation provides a typical profile

            tp.load() - will retreive a list of temps from the settings

            tp.tempNow() - will return the current target temp
            
    """
    def __init__(self):
        self.weekdays=[[0,17],
                       [5,17],
                       [6,23],
                       [7,23],
                       [8,23],
                       [9,21],
                       [10,20],
                       [12,20],
                       [14,20],
                       [16,20],
                       [17,22],
                       [18,23],
                       [19,23],
                       [20,23],
                       [21,22],
                       [22,21],
                       [23,19],
                       [23.5,17]]
        self.weekends=self.weekdays
        
    def load(self):
        if not settings.weekdays:
            settings.weekdays=self.weekdays
            settings.weekends=self.weekends
        self.weekdays=settings.weekdays
        self.weekends=settings.weekends

    def save(self):
        settings.weekdays=self.weekdays
        settings.weekends=self.weekends
        

    def hoursToTemp(self,hours,dayprofile):
        # Find the points to use for interpolation either side of this time
        
        lasttime=dayprofile[-1][0] # might be after the last time in the day profile
        if hours>=lasttime:
            nextpoint_time,nextpoint_temp=dayprofile[0]
            nextpoint=[nextpoint_time+24,nextpoint_temp]
            prevpoint=dayprofile[-1]
        elif hours<=dayprofile[0][0]:# might be before the first point in the day
            nextpoint=dayprofile[0]
            prevpoint_time,prevpoint_temp=dayprofile[-1]
            prevpoint=[prevpoint_time-24,prevpoint_temp]
        else: # In between the rest of the times
            for i in range(len(dayprofile)-1):# test intervals
                if dayprofile[i][0]<=hours<=dayprofile[i+1][0]:
                    prevpoint=dayprofile[i]
                    nextpoint=dayprofile[i+1]
                    #logging.info("Found at index %s as hours is %s and hour[i] is %s" % (i,hours,dayprofile[i][0]))
                    break
        # Interpolate between prevpoint and nextpoint
        #logging.info("Time: %s\nPrevious point: %s\nNextPoint: %s\n\n" % (hours,prevpoint,nextpoint))
        prop_next=1.0*(hours-prevpoint[0])/(nextpoint[0]-prevpoint[0])
        temp=prevpoint[1]*(1-prop_next)+nextpoint[1]*prop_next
        return temp
        
        
    def timeToTemp(self,now):
        """
            Returns an interpolated temperature for a number of
            hours through the day
        """
        if now.weekday()>4:
            dayprofile=self.weekdays
            logging.info("It's a weekday")
        else:
            dayprofile=self.weekends
            logging.info("It's a weekend")
        # Get the time in the day as hours and fraction of hours
        hours=now.hour+now.minute/60.0
        return self.hoursToTemp(hours,dayprofile)

    def tempNow(self):
        # Calculates an interpolated temperature target based
        # on the day of the week and time of day
        now=datetime.now()
        temp=self.timeToTemp(now)
        return temp

    def bothProfilesAsJSON(self):
        pair='{"weekdays":%s,"weekends":%s}' % (self.weekdays,self.weekdays)
        return pair

    def setSlider(self,daytype,hour,temp):

        logging.info("updating a temp for %s o'clock to %s deg c" % (hour,temp))
        changed=False
        if daytype=="weekends":
            logging.info("weekend temp change")
            for i in range(len(self.weekends)):
                if str(self.weekends[i][0])==hour:
                    if not self.weekends[i][1]==temp:
                        logging.info("Updated weekend temp")
                        self.weekends[i][1]=float(temp)
                        changed=True
                        break
            else:
                return "FAILED"
        else:
            logging.info("weekday temp change")
            for i in range(len(self.weekdays)):
                if str(self.weekdays[i][0])==hour:
                    logging.info("found time")
                    if not self.weekdays[i][1]==temp:
                        logging.info("Updated weekday temp")
                        self.weekdays[i][1]=float(temp)
                        changed=True
                        break
            else:
                return "FAILED"



        if changed:
            logging.info("updating stored values")
            self.save()
            
        
        

        
                    
        
        
        

class MainPage(webapp2.RequestHandler):
    def get(self):

        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
            
        template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }
        if user and "french" in user.email():
            template_values["targ_temp"]="%.1f" %temp_profiles.tempNow()
            template_values["act_temp"]=settings.actual_temp
            template = JINJA_ENVIRONMENT.get_template('statics/programmer.html')
        else:
            template = JINJA_ENVIRONMENT.get_template('statics/needtologin.html')
        self.response.write(template.render(template_values))
            
class GetBothProfilesAsJSON(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Contet-Type']='application/json'
        self.response.write(temp_profiles.bothProfilesAsJSON())

class GetCurrentTemperature(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type']='application/json'
        self.response.write(temp_profiles.tempNow())

class SetSlider(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        email=user.email()
        logging.info(email)
        if "french" in email:
            logging.info("allowed")
            profile=self.request.get("profile")
            hour=self.request.get("hour")
            temp=self.request.get("temp")
            logging.info("Processing slider request")
            temp_profiles.setSlider(profile,hour,temp)
            self.response.headers['Content-Type']='application/json'
            self.response.write('"OK"')
        else:
            self.response.write("NOT LOGGED IN")
        
class ReportActual(webapp2.RequestHandler):
    def get(self):
        actual_temp=self.request.get("actual_temp")
        settings.actual_temp=actual_temp
        
        
        
app = webapp2.WSGIApplication([
    ('/bothprofilesjson',GetBothProfilesAsJSON),
    ('/getcurrenttemp',GetCurrentTemperature),
    ('/setslider',SetSlider),
    ('/reportactual',ReportActual),
    ('/', MainPage),
], debug=True)
      
logging.info("Loading up the settings")
settings=Settings(maxage=10)# Load the application settings
settings.refresh()
logging.info("Set up initial profile")
temp_profiles=TempProfiles()
temp_profiles.load()
                       
                       



