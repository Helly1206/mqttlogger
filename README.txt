mqttlogger v0.8.0

mqttlogger - logging of MQTT traffic
========== = ======= == ==== =======

Use of xml file to setup logging:
/etc/mqttlogger.xml

<!--This XML file describes the topics to log.
            Add an item to add a log file.
            <logger> Main element, do not change name
                <broker> Address of MQTT broker
                <port> MQTT port
                <username> MQTT username
                <password> MQTT password
                <item> Item to log, enter name of item here, e.g. mydevice
                    <folder> Path to store logfiles
                    <maintopic> Main topic to log
                    <topic1> First topic to log (may contain wildcards)
                    <topic2> Second topic to log
                    ...
                    <topicn> nth topic to log-->

Runs as service:

sudo systemctl start/stop/status mqttlogger.service

mqttlogger.py: logging of MQTT traffic
Usage:
    mqttlogger.py <arguments>
        -h, --help    : Display this help
        -v, --version : Display version
        -d, --debug   : Debug communication
        <no arguments>: run as daemon

That's all for now ...

Please send Comments and Bugreports to hellyrulez@home.nl
