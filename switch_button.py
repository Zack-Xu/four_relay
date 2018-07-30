from SimpleIO import Switch
from Config import Config
from StateMQTTClient import StateMQTTClient
from IrqLongpressReset import IrqLongpressReset
from ubinascii import hexlify
import network
import machine
import utime
import micropython

ap_if = network.WLAN(network.AP_IF)
sta_if = network.WLAN(network.STA_IF)

RESET_PIN = 4
LED_PIN = 5
RELAY_PIN_1 = 12
RELAY_PIN_2 = 13
RELAY_PIN_3 = 15
RELAY_PIN_4 = 14
botton1_pin= 2



PROGRAM_NAME = 'switch_button'
DEVICE_NAME = 'Pili_Relay' + hexlify(ap_if.config("mac")[-3:]).decode()+"_"

#DEVICENAME MQTT设备ID

# JSON格式转换？
CONFIG_DATA_SCHEMA = """
{"name": "%s",
"command_topic": "%s",
"state_topic": "%s",
"availability_topic": "%s"
}
"""

BASE_TOPIC = 'HA/switch/piliboard/' + DEVICE_NAME
AVAILABILITY_TOPIC = BASE_TOPIC + "/availability"


#设置对应设备的Command和State地址

COMMAND_TOPIC1 = BASE_TOPIC+"1" + "/command"
STATE_TOPIC1 = BASE_TOPIC+"1" + "/state"
COMMAND_TOPIC2 = BASE_TOPIC+"2" + "/command"
STATE_TOPIC2 = BASE_TOPIC+"2" + "/state"
COMMAND_TOPIC3 = BASE_TOPIC+"3" + "/command"
STATE_TOPIC3 = BASE_TOPIC+"3" + "/state"
COMMAND_TOPIC4 = BASE_TOPIC+"4" + "/command"
STATE_TOPIC4 = BASE_TOPIC+"4" + "/state"





#设置自动发现地址
CONFIG_TOPIC1 = 'homeassistant/switch/piliboard/' + DEVICE_NAME+"1"  + '/config'
CONFIG_TOPIC2 = 'homeassistant/switch/piliboard/' + DEVICE_NAME+"2"  + '/config'
CONFIG_TOPIC3 = 'homeassistant/switch/piliboard/' + DEVICE_NAME+"3"  + '/config'
CONFIG_TOPIC4 = 'homeassistant/switch/piliboard/' + DEVICE_NAME+"4"  + '/config'



CONFIG_DATA1 = CONFIG_DATA_SCHEMA % (DEVICE_NAME+"1",
                                    COMMAND_TOPIC1,
                                    STATE_TOPIC1,
                                    AVAILABILITY_TOPIC,
                                    )
CONFIG_DATA2 = CONFIG_DATA_SCHEMA % (DEVICE_NAME+"2" ,
                                    COMMAND_TOPIC2,
                                    STATE_TOPIC2,
                                    AVAILABILITY_TOPIC,
                                    )
CONFIG_DATA3 = CONFIG_DATA_SCHEMA % (DEVICE_NAME+"3" ,
                                    COMMAND_TOPIC3,
                                    STATE_TOPIC3,
                                    AVAILABILITY_TOPIC,
                                    )
CONFIG_DATA4 = CONFIG_DATA_SCHEMA % (DEVICE_NAME+"4",
                                    COMMAND_TOPIC4,
                                    STATE_TOPIC4,
                                    AVAILABILITY_TOPIC,
                                    )





MqttClient = None
mqtt_conf = Config()

RELAY_1= Switch( led_num=RELAY_PIN_1)
RELAY_2= Switch( led_num=RELAY_PIN_2)
RELAY_3= Switch( led_num=RELAY_PIN_3)
RELAY_4= Switch( led_num=RELAY_PIN_4)
botton = machine.Pin(botton1_pin, machine.Pin.IN,machine.Pin.PULL_UP)


def mqtt_start():
    MqttClient.connect()
    if MqttClient.connected:
        print("mqtt connected: subto {b}".format(b=COMMAND_TOPIC1))
        print("mqtt connected: subto {b}".format(b=COMMAND_TOPIC2))
        print("mqtt connected: subto {b}".format(b=COMMAND_TOPIC3))
        print("mqtt connected: subto {b}".format(b=COMMAND_TOPIC4))

        
        MqttClient.publish( CONFIG_TOPIC1, CONFIG_DATA1.encode(), retain=True)
        MqttClient.publish( CONFIG_TOPIC2, CONFIG_DATA2.encode(), retain=True)
        MqttClient.publish( CONFIG_TOPIC3, CONFIG_DATA3.encode(), retain=True)
        MqttClient.publish( CONFIG_TOPIC4, CONFIG_DATA4.encode(), retain=True)
        
        MqttClient.subscribe(COMMAND_TOPIC1)
        MqttClient.subscribe(COMMAND_TOPIC2)
        MqttClient.subscribe(COMMAND_TOPIC3)
        MqttClient.subscribe(COMMAND_TOPIC4)
        
        MqttClient.publish( AVAILABILITY_TOPIC, b"online", retain=True)
       
        
        MqttClient.publish( STATE_TOPIC1, RELAY_1._state.encode(), retain=True )
        MqttClient.publish( STATE_TOPIC2, RELAY_2._state.encode(), retain=True )
        MqttClient.publish( STATE_TOPIC3, RELAY_3._state.encode(), retain=True )
        MqttClient.publish( STATE_TOPIC4, RELAY_4._state.encode(), retain=True )
        return True
    else:
        print("Can't connect to MQTT Broker")
        return False


def mqtt_cb(topic, msg):
    print((topic, msg))

    if topic==COMMAND_TOPIC1.encode():
        change_stat(msg,RELAY_1,STATE_TOPIC1);
    if topic==COMMAND_TOPIC2.encode():
        change_stat(msg,RELAY_2,STATE_TOPIC2);
    if topic==COMMAND_TOPIC3.encode():
        change_stat(msg,RELAY_3,STATE_TOPIC3);
    if topic==COMMAND_TOPIC4.encode():
        change_stat(msg,RELAY_4,STATE_TOPIC4);

def change_stat(msg,relay,topic):
    if msg == b"ON":
        relay.turn_on()
    elif msg == b"OFF":
        relay.turn_off()
    MqttClient.publish( topic, relay._state.encode(), retain=True )



def mqtt_init(conf):
    global MqttClient

    if (conf == None) or not('mqtt_ip' in conf):
        MqttClient = StateMQTTClient(DEVICE_NAME, None)
        return False

    port=1883
    try:
        port=int(conf.get("mqtt_port"))
    except:
        print("MQTT Input port error, let it be 1883, and continue...")
        
    MqttClient = StateMQTTClient(DEVICE_NAME, conf.get("mqtt_ip"), port=port, user=conf.get("mqtt_user"), password=conf.get("mqtt_password"), keepalive=60)
    MqttClient.set_callback(mqtt_cb)
    MqttClient.set_last_will( AVAILABILITY_TOPIC, b"offline", retain=True)
    return True

def toggle():
    print('pressed')
    
def toggle1(v):
    RELAY_1.toggle()
    MqttClient.publish( STATE_TOPIC1, RELAY_1._state.encode(), retain=True )
    print('pressed A')
    


def start():
    irq = IrqLongpressReset(pin_no=RESET_PIN, led_pin_no=LED_PIN, main_module=PROGRAM_NAME, press_action=toggle, device_name=DEVICE_NAME)
    botton.irq(trigger=machine.Pin.IRQ_FALLING, handler=toggle1)
    last_try_time1 = 0
    last_try_time2 = 0
    last_resp_time = utime.time()

    ap_if.active(False)
    sta_if.active(True)
    if mqtt_init(mqtt_conf.content):
        utime.sleep(5)
        mqtt_start()
    else:
        print("mqtt_init failed")
        return
    

    while True :
        if not sta_if.isconnected():
            print("Can't connect to WIFI")
            utime.sleep(3)

        elif not MqttClient.connected:
            now = utime.time()
            last_resp_time = now
            delta = now - last_try_time1
            if delta > 10:
                last_try_time1 = now
                mqtt_start()
                micropython.mem_info()

        else:
            if MqttClient.check_msg()==1:
                last_resp_time = utime.time()
            now = utime.time()
            if now-last_resp_time > 20:
                print("No mqtt ping response, disconnect it")
                MqttClient.disconnect()
                continue

            delta = now - last_try_time2
            if delta > 10:
                MqttClient.ping()
                last_try_time2 = now
                micropython.mem_info()
