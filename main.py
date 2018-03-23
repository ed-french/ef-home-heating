import webapp2,json,logging

from settings import Settings
from datetime import datetime

"""
    Simple Programmable thermostat server-side application

    Provides GUI to modify the program easily

    The main page is provided from a static file

    The profiles are retreived and ammended via json endpoints:

    /bothprofilesjson retreives the temperature profiles and any other settings

    




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
        hours=now.hour+now.minte/60.0
        return hoursToTemp(hours,dayprofile)

    def tempNow(self):
        # Calculates an interpolated temperature target based
        # on the day of the week and time of day
        now=datetime.now()
        temp=self.timeToTemp(now)
        return temp

    def bothProfilesAsJSON(self):
        pair={"weekdays":self.weekdays,"weekends":self.weekends}
        return pair


        
                    
        
        
        

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Hello, World!')
        self.response.write(settings.weekdays)

        for i in range(0,int(23.75*4)):
            self.response.write("%s > %s \n" % (i/4.0,temp_profiles.hoursToTemp(i/4.0,settings.weekdays)))
            
class GetBothProfilesAsJSON(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Contet-Type']='application/json'
        self.response.write(temp_profiles.bothProfilesAsJSON())
        
app = webapp2.WSGIApplication([
    ('/bothprofilesjson',GetBothProfilesAsJSON),
    ('/', MainPage),
], debug=True)
      
logging.info("Loading up the settings")
settings=Settings()# Load the application settings
settings.refresh()
logging.info("Set up initial profile")
temp_profiles=TempProfiles()
temp_profiles.load()
                       
                       



