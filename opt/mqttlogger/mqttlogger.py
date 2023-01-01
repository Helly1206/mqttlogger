#!/usr/bin/python3

# -*- coding: utf-8 -*-
#########################################################
# SERVICE : mqttlogger.py                               #
#           Simple logger of MQTT traffic               #
#           To be used for debugging or visualizing     #
#           I. Helwegen 2022                            #
#########################################################

####################### IMPORTS #########################
import sys
import os
import signal
import shutil
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString
from uuid import getnode
from datetime import datetime
try:
    import paho.mqtt.client as mqttclient
    ifinstalled = True
except ImportError:
    ifinstalled = False

#########################################################

####################### GLOBALS #########################
VERSION      = "0.80"
XML_FILENAME = "mqttlogger.xml"
ENCODING     = 'utf-8'
HEADER_EXT   = "_header.csv"
LOG_EXT      = "_log.csv"
MAXFILES     = 8
#########################################################

###################### FUNCTIONS ########################

#########################################################
# Class : database                                      #
#########################################################
class database(object):
    def __init__(self):
        self.db = {}
        if not self.getXMLpath(False):
            # only create xml if super user, otherwise keep empty
            self.createXML()
            self.getXML()
        else:
            self.getXML()

    def __del__(self):
        del self.db
        self.db = {}

    def __call__(self):
        return self.db

    def update(self):
        self.updateXML()

    def reload(self):
        del self.db
        self.db = {}
        self.getXML()

    def bl(self, val):
        retval = False
        try:
            f = float(val)
            if f > 0:
                retval = True
        except:
            if val.lower() == "true" or val.lower() == "yes" or val.lower() == "1":
                retval = True
        return retval

################## INTERNAL FUNCTIONS ###################

    def gettype(self, text, txtype = True):
        try:
            retval = int(text)
        except:
            try:
                retval = float(text)
            except:
                if text:
                    if text.lower() == "false":
                        retval = False
                    elif text.lower() == "true":
                        retval = True
                    elif txtype:
                        retval = text
                    else:
                        retval = ""
                else:
                    retval = ""

        return retval

    def settype(self, element):
        retval = ""
        if type(element) == bool:
            if element:
                retval = "true"
            else:
                retval = "false"
        elif element != None:
            retval = str(element)

        return retval

    def getXML(self):
        XMLpath = self.getXMLpath()
        try:
            tree = ET.parse(XMLpath)
            root = tree.getroot()
            self.db = self.parseKids(root, True)
        except Exception as e:
            print("Error parsing xml file")
            print("Check XML file syntax for errors")
            print(e)
            exit(1)

    def parseKids(self, item, isRoot = False):
        db = {}
        if self.hasKids(item):
            for kid in item:
                if self.hasKids(kid):
                    db[kid.tag] = self.parseKids(kid)
                else:
                    db.update(self.parseKids(kid))
        elif not isRoot:
            db[item.tag] = self.gettype(item.text)
        return db

    def hasKids(self, item):
        retval = False
        for kid in item:
            retval = True
            break
        return retval

    def updateXML(self):
        db = ET.Element('logger')
        pcomment = self.getXMLcomment("")
        if pcomment:
            comment = ET.Comment(pcomment)
            db.append(comment)
        self.buildXML(db, self.db)

        XMLpath = self.getXMLpath(dowrite = True)

        with open(XMLpath, "w") as xml_file:
            xml_file.write(self.prettify(db))

    def buildXML(self, xmltree, item):
        if isinstance(item, dict):
            for key, value in item.items():
                kid = ET.SubElement(xmltree, key)
                self.buildXML(kid, value)
        else:
            xmltree.text = self.settype(item)

    def createXML(self):
        print("Creating new XML file")
        db = ET.Element('logger')
        comment = ET.Comment("This XML file describes the topics to log.\n"
        "            Add an item to add a log file.\n"
        "            <logger> Main element, do not change name\n"
        "                <broker> Address of MQTT broker\n"
        "                <port> MQTT port\n"
        "                <username> MQTT username\n"
        "                <password> MQTT password\n"
        "                <item> Item to log, enter name of item here, e.g. mydevice\n"
        "                    <folder> Path to store logfiles\n"
        "                    <maintopic> Main topic to log\n"
        "                    <topic1> First topic to log (may contain wildcards)\n"
        "                    <topic2> Second topic to log\n"
        "                    ...\n"
        "                    <topicn> nth topic to log")
        db.append(comment)

        XMLpath = self.getNewXMLpath()

        with open(XMLpath, "w") as xml_file:
            xml_file.write(self.prettify(db))

    def getXMLcomment(self, tag):
        comment = ""
        XMLpath = self.getXMLpath()
        with open(XMLpath, 'r') as xml_file:
            content = xml_file.read()
            if tag:
                xmltag = "<{}>".format(tag)
                xmlend = "</{}>".format(tag)
                begin = content.find(xmltag)
                end = content.find(xmlend)
                content = content[begin:end]
            cmttag = "<!--"
            cmtend = "-->"
            begin = content.find(cmttag)
            end = content.find(cmtend)
            if (begin > -1) and (end > -1):
                comment = content[begin+len(cmttag):end]
        return comment

    def prettify(self, elem):
        """Return a pretty-printed XML string for the Element.
        """
        rough_string = ET.tostring(elem, ENCODING)
        reparsed = parseString(rough_string)
        return reparsed.toprettyxml(indent="\t").replace('<?xml version="1.0" ?>','<?xml version="1.0" encoding="%s"?>' % ENCODING)

    def getXMLpath(self, doexit = True, dowrite = False):
        etcpath = "/etc/"
        XMLpath = ""
        # first look in etc
        if os.path.isfile(os.path.join(etcpath,XML_FILENAME)):
            XMLpath = os.path.join(etcpath,XML_FILENAME)
            if dowrite and not os.access(XMLpath, os.W_OK):
                print("No valid writable XML file location found")
                print("XML file cannot be written, please run as super user")
                if doexit:
                    exit(1)
        else: # Only allow etc location
            print("No XML file found")
            if doexit:
                exit(1)
        return XMLpath

    def getNewXMLpath(self):
        etcpath = "/etc/"
        XMLpath = ""
        # first look in etc
        if os.path.exists(etcpath):
            if os.access(etcpath, os.W_OK):
                XMLpath = os.path.join(etcpath,XML_FILENAME)
        if (not XMLpath):
            print("No valid writable XML file location found")
            print("XML file cannot be created, please run as super user")
            exit(1)
        return XMLpath


#########################################################

#########################################################
# Class : mqttlogger                                    #
#########################################################
class mqttlogger(object):
    def __init__(self):
        self.name         = ""
        self.client       = None
        self.connected    = False
        self.rcConnect    = 0
        self.rcDisconnect = 0
        self.debug        = False
        self.headers      = {}
        self.values       = {}
        signal.signal(signal.SIGINT, self.exit_app)
        signal.signal(signal.SIGTERM, self.exit_app)

    def __del__(self):
        pass

    def __str__(self):
        return "{}: logging of MQTT traffic".format(self.name)

    def __repr__(self):
        return self.__str__()

    def run(self, argv):
        if len(os.path.split(argv[0])) > 1:
            self.name = os.path.split(argv[0])[1]
        else:
            self.name = argv[0]

        self.db = database()

        index = 0
        for arg in argv:
            if arg[0] == "-":
                if arg == "-h" or arg == "--help":
                    self.printHelp()
                    exit()
                elif arg == "-v" or arg == "--version":
                    print(self)
                    print("Version: {}".format(VERSION))
                    exit()
                elif arg == "-d" or arg == "--debug":
                    self.debug = True
                    del argv[index]
                else:
                    self.parseError(arg)
            index += 1
        if len(argv) < 2:
            if not ifinstalled:
                print(self)
                print("MQTT not installed")
                print("Please install paho mqtt: pip3 install paho-mqtt")
                print("Terminating")
                exit(1)
            self.daemon()
        else:
            self.parseError(argv[1])

    def printHelp(self):
        print(self)
        print("Usage:")
        print("    {} {}".format(self.name, "<arguments>"))
        print("        -h, --help    : Display this help")
        print("        -v, --version : Display version")
        print("        -d, --debug   : Debug communication")
        print("        <no arguments>: run as daemon")
        print("")

    def parseError(self, opt = ""):
        print(self)
        print("Invalid option entered")
        if opt:
            print(opt)
        print("Enter '{} -h' for help".format(self.name))
        exit(1)

    def daemon(self):
        self.client = mqttclient.Client("mqttlogger_" + format(getnode(),'X')[-6:])  #create new instance
        self.client.on_message=self.onmessage #attach function to callback
        self.client.on_connect=self.onconnect  #bind call back function
        self.client.on_disconnect=self.ondisconnect  #bind call back function
        self.client.on_log=self.onlog

        if not "broker" in self.db().keys():
            print("No broker entered, terminating")
            exit(1)
        elif not self.db()["broker"]:
            print("Empty broker entered, terminating")
            exit(1)
        else:
            if "port" in self.db().keys():
                port = self.db()["port"]
            else:
                port = 1883
            if "username" in self.db().keys():
                if self.db()["username"]:
                    password = None
                    if "password" in self.db().keys():
                        if self.db()["password"]:
                            password = self.db()["password"]
                    self.client.username_pw_set(self.db()["username"], password=password)

            try:
                self.client.connect(self.db()["broker"], port=port) #connect to broker
                self.client.loop_start() #start the loop
            except:
                print("Invalid connection, check server address")
                exit(1)

        for item, value in self.db().items():
            if type(value) is dict:
                if "maintopic" in value.keys():
                    if value["maintopic"]:
                        maintopic = value["maintopic"] + '/' if not value["maintopic"].endswith('/') else value["maintopic"]
                        for topic, topval in value.items():
                            if topic.startswith("topic"):
                                self.client.subscribe(maintopic + topval)
                        self.headers[item] = ["timestamp", "date", "time"]
                        self.values[item] = {}
                        if os.path.exists(self.headerPath(item)):
                            self.copyFile(self.headerPath(item))
                            os.remove(self.headerPath(item)) # move to .1,, .2 etc later
                        if os.path.exists(self.logPath(item)):
                            self.copyFile(self.logPath(item))
                            os.remove(self.logPath(item)) # move to .1,, .2 etc later

        signal.pause()

    def exit_app(self, signum, frame):
        print("Terminating ...")
        pass

    def onlog(self, client, userdata, level, buf):
        if self.debug:
            print(buf)

    def onmessage(self, client, userdata, message):
        rind = message.topic.rindex("/")
        maintopic = ""
        if rind > -1:
            maintopic = message.topic[:rind]

        item = None
        value = {}
        for item, value in self.db().items():
            if type(value) is dict:
                if "maintopic" in value.keys():
                    if value["maintopic"]:
                        maintopic2 = value["maintopic"][:-1] if value["maintopic"].endswith('/') else value["maintopic"]
                        if maintopic == maintopic2:
                            break
        if item and value:
            if not message.topic in self.headers[item]:
                self.headers[item].append(message.topic)
                self.writeheader(item)
            self.values[item][message.topic] = message.payload.decode('utf-8')
            self.writelog(item)

    def onconnect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected OK, Returned code = " + str(rc))
            self.connected = True
            self.rcDisconnect = 0
        else:
            if self.rcConnect != rc:
                print("Bad connection, Returned code = " + str(rc))
            self.connected = False
        self.rcConnect = rc

    def ondisconnect(self, client, userdata, rc):
        if rc == 0 or self.rcDisconnect != rc:
            print("Disconnected, Returned code = " + str(rc))
            self.rcConnect = 0
        self.connected = False
        self.rcDisconnect = rc

    def writeheader(self, item):
        csvstr = ""
        for head in self.headers[item]:
            if csvstr:
                csvstr += ", "
            csvstr += head
        csvstr += "\n"
        try:
            with open(self.headerPath(item), "w") as f:
                f.write(csvstr)
        except:
            print(csvstr)

    def writelog(self, item):
        now = datetime.now()
        tmepoch = str(int(now.timestamp()))
        tmdate = now.strftime("%d-%m-%Y")
        tmtime = now.strftime("%H:%M:%S")
        csvstr = ""
        for head in self.headers[item]:
            if csvstr:
                csvstr += ", "
            if head == "timestamp":
                csvstr += tmepoch
            elif head == "date":
                csvstr += tmdate
            elif head == "time":
                csvstr += tmtime
            else:
                csvstr += self.values[item][head]
        csvstr += "\n"
        try:
            with open(self.logPath(item), "a") as f:
                f.write(csvstr)
        except:
            print(csvstr)

    def headerPath(self, item):
        maintopic = self.db()[item]["maintopic"][:-1] if self.db()[item]["maintopic"].endswith('/') else self.db()[item]["maintopic"]
        fname = maintopic.replace("/","_") + HEADER_EXT
        return os.path.join(self.db()[item]["folder"], fname)

    def logPath(self, item):
        maintopic = self.db()[item]["maintopic"][:-1] if self.db()[item]["maintopic"].endswith('/') else self.db()[item]["maintopic"]
        fname = maintopic.replace("/","_") + LOG_EXT
        return os.path.join(self.db()[item]["folder"], fname)

    def copyFile(self, path):
        for i in range(MAXFILES-1, -1, -1):
            if i == 0:
                cpsrc = path
            else:
                cpsrc = path + "." + str(i)
            cpdst = path + "." + str(i+1)
            try:
                shutil.copyfile(cpsrc, cpdst)
            except:
                pass

######################### MAIN ##########################
if __name__ == "__main__":
    mqttlogger().run(sys.argv)
