mqtt433MHz v0.8.0

mqtt433MHz - 433 MHz to MQTT translator
========== = ======= == ==== ==========

Also creates Home Assistant auto discovery message.
At the moment only switches (433Mhz output) and events (433MHz input) are supported

Use of xml file to setup logging:
/etc/mqtt433MHz.xml

<!--This XML file describes the topics to relay.
            Add an item to add a relay.
            <mqtt433MHz> Main element, do not change name
                <broker> Address of MQTT broker
                <port> MQTT port
                <username> MQTT username
                <password> MQTT password
                <hatopic> home assistant topic (default homeassistant)
                <devices>
                    <device1> devicename is key
                        <RFout> true if output device, false if input device
                        <item433>
                            <SysCode> 433MHz sys-code
                            <GroupCode> 433MHz group-code (if used)
                            <DeviceCode> 433MHz device-code
                        <hadevice>  (ids is autogenerated)
                            <name> device name
                            <mf> manufacturer
                            <mdl> model
                        <itemmqtt>
                            <maintopic> main mqtt topic for device
                            <cmd_t> only for output device
                            <stat_t> only for input device, for output device the current value is copied
                        <hatype> switch or event
                        <hadisco> (uniq_id, pl_off, pl_on is autogenerated)
                            <name> just a name
                            <dev_cla> none if omitted, outlet or switch (only for switch), doorbell or button (only for event)
                    <device2> ... -->
                
  jDeviceString.AddArray("ids", arraystr, 1);
  jDeviceString.AddItem("name", devName);
  jDeviceString.AddItem("mf", String(dev_mf));
  jDeviceString.AddItem("mdl", String(dev_mdl));                      
     
  // binary_sensor                   
                        
  jString.AddItem("name", ha_up.name);
  jString.AddItem("~", settings.getString(settings.mainTopic));
  jString.AddItem("cmd_t", "~/up");
  jString.AddItem("pl_prs", "1");
  jString.AddItem("uniq_id", arraystr[1] + us(ha_up.id));
  jString.AddItem("dev", jDeviceString);
  //logger.printf(jString.GetJson());

  topic = joinTopic(joinTopic(joinTopic(settings.getString(settings.haTopic), ha_up.type), devName + us(ha_up.id)), ha_config);
  client.publish(topic.c_str(), jString.GetJson().c_str(), true);
  
  // switch
  
  jString.AddItem("name", ha_blind.name);
  jString.AddItem("~", settings.getString(settings.mainTopic));
  jString.AddItem("dev_cla", ha_blind.cla);
  jString.AddItem("cmd_t", "~/updown");
  jString.AddItem("pl_on", "1");
  jString.AddItem("pl_off", "0"); 
  jString.AddItem("uniq_id", arraystr[1] + us(ha_blind.id));
  jString.AddItem("dev", jDeviceString);
  //logger.printf(jString.GetJson());

  topic = joinTopic(joinTopic(joinTopic(settings.getString(settings.haTopic), ha_blind.type), devName + us(ha_blind.id)), ha_config);
  client.publish(topic.c_str(), jString.GetJson().c_str(), true);

Runs as service:

sudo systemctl start/stop/status mqtt433MHz.service

mqtt433MHz.py: 433 MHz to MQTT translator
Usage:
    mqtt433MHz.py <arguments>
        -h, --help    : Display this help
        -v, --version : Display version
        -d, --debug   : Debug communication
        <no arguments>: run as daemon

That's all for now ...

Please send Comments and Bugreports to hellyrulez@home.nl
