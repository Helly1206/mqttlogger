#!/usr/bin/python3

# -*- coding: utf-8 -*-
#########################################################
# SERVICE : mqtt433MHz.py                               #
#           Simple relay of 433MHz signal to MQTT       #
#                                                       #
#           I. Helwegen 2023                            #
#########################################################

####################### IMPORTS #########################
import sys
import os
import signal
import time
import json
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString
from uuid import getnode
try:
    import paho.mqtt.client as mqttclient
    ifinstalled = True
except ImportError:
    ifinstalled = False
try:
    from Pi433MHzif import Pi433MHzif
    if433installed = True                     
except ImportError:
    if433installed = False

#########################################################

####################### GLOBALS #########################
VERSION      = "0.80"
XML_FILENAME = "mqtt433MHz.xml"
ENCODING     = 'utf-8'
CONFIG       = "config"
SLEEPTIME    = 0.1
QOS          = 0
RETAIN       = True
RETAINEVENT  = False
HASTATUS     = "status"
HAONLINE     = "online"
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
        db = ET.Element('mqtt433MHz')
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
        db = ET.Element('mqtt433MHz')
        comment = ET.Comment("This XML file describes the topics to relay.\n"
        "            Add an item to add a relay.\n"
        "            <mqtt433MHz> Main element, do not change name\n"
        "                <broker> Address of MQTT broker\n"
        "                <port> MQTT port\n"
        "                <username> MQTT username\n"
        "                <password> MQTT password\n"
        "                <hatopic> home assistant topic (default homeassistant)\n"
        "                <devices>\n"
        "                    <device1> devicename is key\n"
        "                        <RFout> true if output device, false if input device\n"
        "                        <item433>\n"
        "                            <SysCode> 433MHz sys-code\n"
        "                            <GroupCode> 433MHz group-code (if used)\n"
        "                            <DeviceCode> 433MHz device-code\n"
        "                        <hadevice>  (ids is autogenerated)\n"
        "                            <name> device name\n"
        "                            <mf> manufacturer\n"
        "                            <mdl> model\n"
        "                        <itemmqtt>\n"
        "                            <maintopic> main mqtt topic for device\n"
        "                            <cmd_t> only for output device\n"
        "                            <stat_t> only for input device, for output device the current value is copied\n"
        "                        <hatype> switch or event\n"
        "                        <hadisco> (uniq_id, pl_off, pl_on is autogenerated)\n"
        "                            <name> just a name\n"
        "                            <dev_cla> none if omitted, outlet or switch (only for switch), doorbell or button (only for event)\n"
        "                    <device2> ... ")
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
# Class : mqtt433MHz                                    #
#########################################################
class mqtt433MHz(object):
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
        self.term         = False

    def __del__(self):
        pass

    def __str__(self):
        return "{}: 433 MHz to MQTT translator".format(self.name)

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
            if not if433installed:
                print(self)
                print("Pi433MHzif not installed")
                print("Please install Pi433MHzif: see https://github.com/helly1206/Pi433MHz")
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
        self.client = mqttclient.Client("mqtt433MHz_" + format(getnode(),'X')[-6:])  #create new instance
        self.client.on_message=self.onmessage #attach function to callback
        self.client.on_connect=self.onconnect  #bind call back function
        self.client.on_disconnect=self.ondisconnect  #bind call back function
        self.client.on_log=self.onlog
        self.client433 = Pi433MHzif.Pi433MHzif()

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
                self.client.connect(self.db()["broker"], port=int(port)) #connect to broker
                self.client.loop_start() #start the loop
            except:
                print("Invalid connection, check server address")
                exit(1)

        ####### Subscribe topics
        for key, topic in self.getCmdTopics().items():
            self.client.subscribe(topic)
            if self.debug:
                print("MQTT: subscribed [" + key + "]: " + topic)
        self.client.subscribe(self.joinTopic(self.db()["hatopic"], HASTATUS))
        
        ####### Write disco topics
        for key, disco in self.getHaDiscos().items():
            self.client.publish(disco["topic"], json.dumps(disco["disco"]), QOS, RETAIN)
            if self.debug:
                print("MQTT: HA Discovery [" + disco["topic"] + "]: " + json.dumps(disco["disco"]))

        read433 = True if len(self.get433Inputs())>0 else False
        res = -1
        array = []
        while not self.term:
            if read433:
                res, array = self.client433.ReadMessage(4)
            if res>0:
                syscode, groupcode, devicecode, val = self.array2code(array)
                value = json.dumps({"event_type": str(val)})
                for key, input in self.get433Inputs().items():
                    if (input["SysCode"] == syscode) and (input["GroupCode"] == groupcode) and (input["DeviceCode"] == devicecode):
                        self.client.publish(input["stat"], value, QOS, RETAINEVENT) # value doesn't matter I geuss, retain should be false 
                        if self.debug:
                            print("433MHz: received: SysCode: " + str(syscode) + ", GroupCode: " + str(groupcode) + ", DeviceCode: " + str(devicecode), " value: " + str(val))
                            print("MQTT: publish event: " + input["stat"] + "/" + value)
                        break
            else:
                time.sleep(SLEEPTIME)     

        #signal.pause()
        if self.client:
            ####self.client.wait_for_publish() # wait for all messages published
            self.client.loop_stop()    #Stop loop
            self.client.disconnect() # disconnect

    def exit_app(self, signum, frame):
        print("Terminating ...")
        self.term = True
        pass

    def onlog(self, client, userdata, level, buf):
        if self.debug:
            print(buf)

    def onmessage(self, client, userdata, message):
        output = {}

        if self.joinTopic(self.db()["hatopic"], HASTATUS) == message.topic:
            if message.payload.decode('utf-8') == HAONLINE:
                if self.debug:
                    print("MQTT: received HA online, issue HA Discovery")
                ####### Write disco topics
                for key, disco in self.getHaDiscos().items():
                    self.client.publish(disco["topic"], json.dumps(disco["disco"]), QOS, RETAIN)
                    if self.debug:
                        print("MQTT: HA Discovery [" + disco["topic"] + "]: " + json.dumps(disco["disco"]))
                return

        for key, topic in self.getCmdTopics().items():
            if topic == message.topic:
                output = self.get433Outputs()[key]
                break
        if output:
            value = message.payload.decode('utf-8')
            self.send433MHz(output["SysCode"], output["GroupCode"], output["DeviceCode"], value)  
            if "stat" in output:
                # as current state is unknown, just copy value to stat
                self.client.publish(output["stat"], value, QOS, RETAIN)
            if self.debug:
                print("MQTT: received cmd: " + output["cmd"] + "/" + str(value))
                print("433MHz: send: SysCode: " + str(output["SysCode"]) + ", GroupCode: " + str(output["GroupCode"]) + ", DeviceCode: " + str(output["DeviceCode"]))
                print("MQTT: publish stat: " + output["stat"] + "/" + str(value))
            
        
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

    def getCmdTopics(self):
        cmdtopics = {}
        for key, device in self.db()["devices"].items():
            try:
                if "cmd_t" in device["itemmqtt"].keys():
                    cmdtopics[key] = self.joinTopic(device["itemmqtt"]["maintopic"],device["itemmqtt"]["cmd_t"])
                elif  "command_topic" in device["itemmqtt"].keys():
                    cmdtopics[key] = self.joinTopic(device["itemmqtt"]["maintopic"],device["itemmqtt"]["command_topic"])
            except:
                pass
        return cmdtopics
    
    def getHaDiscos(self):
        discos = {}
        for key, device in self.db()["devices"].items():
            try:
                disco = {}
                ids = format(getnode(),'X')[-6:]
                dev = device["hadevice"]
                dev["ids"] = [ids + "_" + device["hadisco"]["name"]]
                hadisco = device["hadisco"]
                hadisco["~"] = device["itemmqtt"]["maintopic"]
                hadisco["uniq_id"] = ids + "_" + device["hadisco"]["name"]
                if device["RFout"]:
                    if "cmd_t" in device["itemmqtt"].keys():
                        hadisco["cmd_t"] = self.joinTopic("~",device["itemmqtt"]["cmd_t"])
                    elif "command_topic" in device["itemmqtt"].keys():
                        hadisco["cmd_t"] = self.joinTopic("~",device["itemmqtt"]["command_topic"])
                if "stat_t" in device["itemmqtt"].keys():
                    hadisco["stat_t"] = self.joinTopic("~",device["itemmqtt"]["stat_t"])
                elif "status_topic" in device["itemmqtt"].keys():
                    hadisco["stat_t"] = self.joinTopic("~",device["itemmqtt"]["status_topic"])  
                if device["RFout"]:
                    hadisco["pl_on"] = "1"
                    hadisco["pl_off"] = "0"
                else:
                    hadisco["event_types"] = ["1", "0"]
                hadisco["dev"] = dev
                disco["disco"] = hadisco
                disco["topic"] = self.joinTopic(self.joinTopic(self.joinTopic(self.db()["hatopic"],device["hatype"]), device["hadisco"]["name"] + "_" + device["hadisco"]["dev_cla"]), CONFIG)
                discos[key] = disco
            except:
                pass
        return discos
    
    def get433Inputs(self):
        inputs = {}
        for key, device in self.db()["devices"].items():
            try:
                if not device["RFout"]:
                    input = {}
                    if "stat_t" in device["itemmqtt"].keys():
                        input["stat"] = self.joinTopic(device["itemmqtt"]["maintopic"],device["itemmqtt"]["stat_t"])
                    elif "status_topic" in device["itemmqtt"].keys():
                        input["stat"] = self.joinTopic(device["itemmqtt"]["maintopic"],device["itemmqtt"]["status_topic"])
                    if "SysCode" in device["item433"].keys():
                        input["SysCode"] = device["item433"]["SysCode"]
                    if "GroupCode" in device["item433"].keys():
                        input["GroupCode"] = device["item433"]["GroupCode"]
                    if "DeviceCode" in device["item433"].keys():
                        input["DeviceCode"] = device["item433"]["DeviceCode"]
                    inputs[key] = input
            except:
                pass
        return inputs
    
    def get433Outputs(self):
        outputs = {}
        for key, device in self.db()["devices"].items():
            try:
                if device["RFout"]:
                    output = {}
                    if "cmd_t" in device["itemmqtt"].keys():
                        output["cmd"] = self.joinTopic(device["itemmqtt"]["maintopic"],device["itemmqtt"]["cmd_t"])
                    elif "command_topic" in device["itemmqtt"].keys():
                        output["cmd"] = self.joinTopic(device["itemmqtt"]["maintopic"],device["itemmqtt"]["command_topic"])
                    if "stat_t" in device["itemmqtt"].keys():
                        output["stat"] = self.joinTopic(device["itemmqtt"]["maintopic"],device["itemmqtt"]["stat_t"])
                    elif "status_topic" in device["itemmqtt"].keys():
                        output["stat"] = self.joinTopic(device["itemmqtt"]["maintopic"],device["itemmqtt"]["status_topic"])
                    if "SysCode" in device["item433"].keys():
                        output["SysCode"] = device["item433"]["SysCode"]
                    if "GroupCode" in device["item433"].keys():
                        output["GroupCode"] = device["item433"]["GroupCode"]
                    if "DeviceCode" in device["item433"].keys():
                        output["DeviceCode"] = device["item433"]["DeviceCode"]
                    outputs[key] = output
            except:
                pass
        return outputs

    def joinTopic(self, maintopic, topic):
        return maintopic + "/" + topic

    def send433MHz(self, syscode, groupcode, devicecode, value):
        array = self.code2array(syscode, groupcode, devicecode, value)
        return self.client433.WriteMessage(array, len(array)) 

    def code2array(self, syscode, groupcode, devicecode, value):
        array = []
        if (syscode>0):
            array.append(int(syscode))
        if (groupcode>0):
            array.append(int(groupcode))
        array.append(int(devicecode))
        array.append(int(value))
        return array

    def array2code(self, array):
        size = len(array)
        syscode = 0
        groupcode = 0
        devicecode = 0
        value = 0
        if (size == 2):
            devicecode = array[0]
            value = array[1] 
        else:
            syscode = array[0]
            if (size == 3):
                devicecode = array[1]
                value = array[2]  
            elif (size == 4):
                groupcode = array[1]
                devicecode = array[2]
                value = array[3] 
        return syscode, groupcode, devicecode, value

######################### MAIN ##########################
if __name__ == "__main__":
    mqtt433MHz().run(sys.argv)
