import webapp2,json

from settings import Settings
    


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Hello, World!')

settings=Settings()# Load the application settings
settings.refresh()
if not settings.weekdays:
    settings.weekdays={0:17,
                       5:17,
                       6:23,
                       7:23,
                       8:23,
                       9:21,
                       10:20,
                       12:20,
                       14:20,
                       16:20,
                       17:22,
                       18:23,
                       19:23,
                       20:23,
                       21:22,
                       22:21,
                       23:19,
                       23.5:17}
    settings.weekends={0:17,
                       5:17,
                       6:23,
                       7:23,
                       8:23,
                       9:21,
                       10:20,
                       12:20,
                       14:20,
                       16:20,
                       17:22,
                       18:23,
                       19:23,
                       20:23,
                       21:22,
                       22:21,
                       23:19,
                       23.5:17}
                       
                       


app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)
