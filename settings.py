#!/usr/bin/env python
#
# Copyright 2016 Tangentix Ltd

"""

        App Engine Settings Module
        ==========================

        Provides cached settings for use by App Engine instances in the form of key value pairs


        usage:
                from settings import Settings
        
                settings=Settings()         # Loads up current settings on first try

                settings.thing="helloworld" # Changes or creates a new entry for keyname="thing" in the datastore

                settings.thing              # returns a string value named as keyname="thing" in the datastore


                settings.setmaxage(1500)    # sets up the default maximum age

                settings.forcerefresh()     # Refreshes all the settings unconditionally

        Has hardcoded limit of 1000 settings, but frankly that'd be horrible to use this for!

        If the object presented is a string, a float or an int it is stored as a string representation of such and enttype is set accordingly
        otherwise, e.g. for more complex objects a jsonpickled version is stored (to allow human editing when settings is visited)

        TO DO:
            Switch to storing incoming objects as json serialized versions of themselves, so anyting that will json.dumps will be stored OK
            Then recovery is returns whatever you get from json.loads
            Add GUI to allow settings to be maintained more easily and to reduce the danger of errors with json fields
            
"""

import logging,webapp2,json
from google.appengine.ext import ndb
from datetime import datetime,timedelta



class SettingStore(ndb.Model):
    """
        Used to store a single key value pair of settings
    """
    keyname=ndb.StringProperty()
    value=ndb.TextProperty()# Used to store the value
    enttype=ndb.StringProperty()# Used to store type, if not present then string is assumed


class Settings(object):
    """
        A settings object, contains all the settings 
    """
    def __init__(self,maxage=1000):
        #logging.info("Initialising settings")
        self._maxage=maxage # In seconds
        self._lastloaded=None # Datetime for the last load of the settings
        #self.forcerefresh() # Set up settings first time
        if self._settings=={}:# We have nothing at all so set up the dummy (needed so you can use console to manage)
            logging.warn("No old settings, creating a dummy record- can be deleted once real data is available")
            dummy=SettingStore()
            dummy.keyname="DummyKey"
            dummy.value="DummyValue"
            dummy.put()

    def setone(self,keyname,newvalue):
        """
            Directly sets a single value in both the cached and datastore locations
            without doing a complete refresh
        """
        qry=SettingStore.query(SettingStore.keyname==keyname)
        
        

        
        

        entries=qry.fetch(10)
        #logging.info("Found entries of : %s " % entries)
        if len(entries)==1:
            # Key already exists so needs to be changed
            #logging.info("Modifying keyname: %s to value %s" % (keyname,newvalue))
            entry=entries[0]

            # Validate thta they newvalue matches the enttype
            if type(newvalue)==int:
                try:
                    newvalue=int(newvalue)
                except ValueError:
                    raise Exception("Could not convert to int")
                else:
                    storevalue=str(newvalue)
            elif type(newvalue)==float:
                try:
                    newvalue=float(newvalue)
                except ValueError:
                    raise Exception("Could not convert to float")
                else:
                    storevalue=str(newvalue)
            elif type(newvalue)==bool:
                try:
                    newvalue=(newvalue=="True")
                except ValueError:
                    raise Exception("Could not cast to bool")
                else:
                    storevalue=str(newvalue)
            else:
                storevalue=str(newvalue)


            # Modify the existing entry
            
            entry.value=storevalue
            entry.put()

        elif len(entries)==0:
            #logging.info( "Creating new setting keyname: %s to newvalue: %s " % (keyname,newvalue))
            # Make new key
            s=SettingStore()
            s.keyname=keyname
            
            if type(newvalue)==int:
                s.enttype="int"
                s.value=str(newvalue)
            elif type(newvalue)==float:
                s.enttype="float"
                s.value=str(newvalue)

            elif type(newvalue)==str:
                s.enttype="string"
                s.value=newvalue
            elif type(newvalue)==bool:
                s.enttype="boolean"
                s.value=str(newvalue)
            else:
                #Assume it is a json serealizable element
                s.enttype="json"
                s.value=json.dumps(newvalue)
                

            s.put()
        else:
            logging.error("Strange- we seem to have %s instances of a settings called %s" % (len(entries),keyname))

        self._settings[keyname]=newvalue# Set local cache of that value
        
    def setmaxage(self,maxage):
        """
            Change the existing maximum age (in seconds) for the cached settings
        """
        self._maxage=maxage
       
        
    def forcerefresh(self):
        """
            Loads the entire set of existing keys and values from the datastore
            regardless of the age or presence of the cached data
        """
        #logging.info( "loading settings from datastore to local cache")
        qry=SettingStore.query()
        sets=qry.fetch(1000)# Return up to 1000 records
        self._lastloaded=datetime.utcnow()
        newsettings={}
        for set in sets:
            if set.enttype=="int":
                val=int(set.value)
            elif set.enttype=="float":
                val=float(set.value)
            elif set.enttype=="boolean":
                val=(set.value==True)
            elif set.enttype=="string":
                val=set.value
            else:
                val=json.loads(set.value)
            newsettings[set.keyname]=val
        self._settings=newsettings # replace the old settings
        #logging.info("Loaded new data into settings")


    def refresh(self):
        """
            Loads or refreshes the cache only if it is stale
        """
        #logging.info( "Non-forced refresh selected")
        if self._lastloaded==None:
            #logging.info("No settings loaded yet, doing so now. settings._lastloaded is: %s.." % self._lastloaded)
            self.forcerefresh()
        elif datetime.utcnow()>(self._lastloaded+timedelta(seconds=self._maxage)):
            #logging.info( "Data in settings older than %s seconds, forcing refresh" % self._maxage)
            self.forcerefresh()
        else:
            #logging.info("Doing nothing as settings were still fresh")
            pass

        
    def __getattr__(self,keyname):
        """
                Attempts to return the setting with the keyname
                1st: If the cache is fresh and the value exists then it is simply returned
                2nd: If not then the cache is refreshed
                
                However, if it still does not exist, then None is returned
        """
        self.refresh()
        res=self._settings.get(keyname,None)
        if not res:
            self.forcerefresh()
            res=self._settings.get(keyname,None)
    
        return res

    def __setattr__(self,keyname,newvalue):
        """
                Attempts to set or update a setting called keyname with the required newvalue

                Works directly on the datastore, then forces a cache refresh
        """
        # Deal with setting instance attributes
        if keyname[0]=="_":
            self.__dict__[keyname]=newvalue
            #print "Set instance attribute name: %s to newvalue: %s" % (keyname,newvalue)
        else:
            self.setone(keyname,newvalue)
            


            # Now refresh all the entries from the datastore into the cache
            self.forcerefresh()


class ShowEntry(webapp2.RequestHandler):
    """
            Allows editing a single entry at a time
    """
    def get(self):
        """
            Entry form
        """
        keyname=self.request.get("keyname")
        qry=SettingStore.query(SettingStore.keyname==keyname)
        entries=qry.fetch(1)
        entry=entries[0]
        if entry.enttype=="int":
            r=self.intform(entry)
        elif entry.enttype=="float":
            r=self.floatform(entry)
        elif entry.enttype=="string":
            r=self.stringform(entry)
        elif entry.enttype=="json":    
            r=self.jsonform(entry)
        elif entry.enttype=="boolean":
            r=self.booleanform(entry)
        else:
            r="<h3>Unsupported type: %s</h3>" % entry
        page="""<!DOCTYPE HTML>
        <html>
        <head>
          <link href="/statics/dist/jsoneditor.css" rel="stylesheet" type="text/css">
          <script src="/statics/dist/jsoneditor.js"></script>

          <style type="text/css">
            #jsoneditor {
              width: 90%%;
              height: 500px;
            }
          </style>
        </head>
            <h2>Setting: %s</h2>
            <form action="/settings/modifysetting/" method="post">
                %s
            <br />
            <input type="submit" value="submit" />
            </form>
            </html>
        """ % (entry.keyname,r)
        self.response.write(page)
    def intform(self,entry):
        """Returns form innerHtml to edit the type: int"""
        r="""
            <input type="hidden" name="enttype" value="int" />
            <input type="hidden" name="keyname" value="%s" />
            <input type="text" length="50" name="value" value="%s" />
            """ % (entry.keyname,entry.value)
        return r
    def booleanform(self,entry):
        """Returns form innerHtml to edit the type: bool"""
        r="""
            <input type="hidden" name="enttype" value="boolean" />
            <input type="hidden" name="keyname" value="%s" />
            <select name="value">
                <option value="True">True</option>
                <option value="False">False</option>
            </select>
            """ % (entry.keyname)
        return r

    def floatform(self,entry):
        """Returns form innerHtml to edit the type: int"""
        r="""
            <input type="hidden" name="enttype" value="float" />
            <input type="hidden" name="keyname" value="%s" />
            <input type="text" length="50" name="value" value="%s" />
            """ % (entry.keyname,entry.value)
        return r
    def stringform(self,entry):
        """Returns form innerHtml to edit the type: int"""
        r="""
            <input type="hidden" name="enttype" value="string" />
            <input type="hidden" name="keyname" value="%s" />
            <input type="text" size="100" name="value" value="%s" />
            """ % (entry.keyname,entry.value)
        return r
    def jsonform(self,entry):
        """Returns form innerHtml to edit the type: int"""
        r="""
            <input type="hidden" name="enttype" value="json" />
            <input type="hidden" name="keyname" value="%s" />
            <div id="jsoneditor"></div>
            <textarea style="enabled:false" id="rawjson" cols="80" rows="5" name="value">%s</textarea>
            <script>
                  // create the editor
                  var container = document.getElementById('jsoneditor');
                  var options = {onChange:changed};
                  var editor = new JSONEditor(container, options);
              

                  // set json
                  var jsonval=JSON.parse(document.getElementById("rawjson").value)
                  editor.set(jsonval);
                  editor.expandAll();
              
            function changed(jsonnew)
            {
                var jsonlive=editor.get();
                //console.log(jsonlive);
                var jsontext=JSON.stringify(jsonlive, null, 2);
                //console.log(jsontext);
                document.getElementById("rawjson").value=jsontext;
            }


            </script>
            """ % (entry.keyname,entry.value)
        return r

class ModifySetting(webapp2.RequestHandler):
    """
        Update a single settings entry
    """
    def post(self):
        enttype=self.request.get("enttype")
        keyname=self.request.get("keyname")
        valtext=self.request.get("value")
        if enttype=="int":
            v=int(valtext)
            value=valtext
        elif enttype=="float":
            v=float(valtext)
            value=valtext
        elif enttype=="string":
            value=valtext
        elif enttype=="json":
            value=valtext
        elif enttype=="boolean":
            assert(valtext in ["False","True"],"Wierd error where somehow a non boolean value was returned from teh form")
            value=valtext
        else:
            raise Exception("Unexpected type from form entry- %s - strange" % enttype)
        
        qry=SettingStore.query(SettingStore.keyname==keyname)
        entries=qry.fetch(1)
        entry=entries[0]
        entry.value=value
        entry.put()
        self.response.write("""<h3>
Updated value of %s</h3><p>New value is:<br />
<pre>%s</pre>
<script>
window.setTimeout(backtolist,3000);
function backtolist()
{
    window.location="/settings";
}
</script>""" % (keyname,value))
class CreateNewForm(webapp2.RequestHandler):
    """
        Renders form to create a new empty setting
    """
    def get(self):
        r="""
            <form action="/settings/createnewentry/">
                Keyname: <input type="text" name="keyname" /><br/>
                Type: <select name="enttype">
                    <option value="int"/>int</option>
                    <option value="float">float</option>
                    <option value="string">string</option>
                    <option value="boolean">boolean</option>
                    <option value="json">json</option>
                    </select><br/>
                    <input type="submit" value="submit" />
            </form>
          """
        self.response.write(r)
class CreateNewEntry(webapp2.RequestHandler):
    """
        Sets up a new empty setting
    """
    def get(self):
        keyname=self.request.get("keyname")
        enttype=self.request.get("enttype")
        newEntity=SettingStore()
        newEntity.keyname=keyname
        newEntity.enttype=enttype
        newEntity.value='"None Yet!"'
        newEntity.put()
        r="""
            <h3>Set up a new setting of keyname: %s and type: %s</h3>
            <script>
                window.setTimeout(backtolist,3000);
                function backtolist()
                {
                    window.location="/settings";
                }
            </script>
        """ % (keyname,enttype)
        self.response.write(r)
class DeleteSetting(webapp2.RequestHandler):
    """
        Deletes a single setting
    """
    def get(self):
        keyname=self.request.get("keyname")
        qry=SettingStore.query(SettingStore.keyname==keyname)
        entries=qry.fetch(1)
        entry=entries[0]
        entry.key.delete()
        r="""<h3>Entry for %s deleted</h3>
                    <script>
                window.setTimeout(backtolist,3000);
                function backtolist()
                {
                    window.location="/settings";
                }
            </script>
        """ % keyname
        self.response.write(r)
class MainHandler(webapp2.RequestHandler):
    """
                Lists and allows editing of the settings
    """
    def get(self):
        """
                List the settings
        """
        entries=self.retreiveAllSettings()
        r="""<html><head>
                <style>
                    
                    td {background-color:#c0c0ff; color:black;}
                    body {background-color:#000030; color:white;}
                    a {background-color:#e0e0ff;color:black;font-size:19pt;}
                
                </style>
                <script>
                    function showDeleteConfirm(keyname)
                    {
                        var row=document.getElementById(keyname);
                        var line='<h3>Do you want to delete? <a href="/settings">No</a> <a href="/settings/deletesetting/?keyname='+keyname
                        line=line+'">Yes</a>';
                        row.innerHTML=line;
                    }
                </script>
            </head><body>
            <h2>Current Settings</h2>
            <table>
                <tr>
                    <th>Index</th><th>Key Name</th><th>Type</th><th>Value</th>
                </tr>
        """
        for i,entry in enumerate(entries):
            if not entry.enttype:
                entry.enttype="string"
                entry.put()
            if entry.enttype=="json":
                show="<pre>%s</pre>" % entry.value
            else:
                show=entry.value
            r+="""<tr id="%s">
                    <td>%s</td><td><a href="/settings/showentry/?keyname=%s">%s</a></td><td>%s</td><td>%s</td><td><a onclick=showDeleteConfirm("%s")>X</a></td></a>
                </tr>""" % (entry.keyname,i,entry.keyname,entry.keyname,entry.enttype,show,entry.keyname)
        r+="""</table>
            <a href="/settings/createnewform/">Create New Entry</a>"""
        self.response.write(r)

    def retreiveAllSettings(self):
        qry=SettingStore.query()
        entries=qry.fetch(250)# Fetch all the settings (250 is maximum!)
        return entries
            
        

app = webapp2.WSGIApplication([
    ('/settings/showentry/',ShowEntry),
    ('/settings/modifysetting/',ModifySetting),
    ('/settings/deletesetting/',DeleteSetting),
    ('/settings/createnewform/',CreateNewForm),
    ('/settings/createnewentry/',CreateNewEntry),
    ('/settings', MainHandler)
], debug=True)





