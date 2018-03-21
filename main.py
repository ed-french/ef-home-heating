import webapp2

from google.cloud import datastore

project_id="ef-home-heating"

def create_client(project_id):
    return datastore.Client(project_id)

def get_settings(project_id):
    client=create_client(project_id)
    query = client.query(kind='settings')
    query.order = ['created']
    return list(query.fetch())

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Hello, World!')
        self.response.write(get_settings(project_id))


app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)
