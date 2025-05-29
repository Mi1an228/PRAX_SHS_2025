# Raspberry Pi Pico W - Blikanie LED s web serverom (MicroPython)
import network
import socket
import time
import _thread
from machine import Pin

led = Pin(25, Pin.OUT)

# Globálne premenné
led_on = True
interval = 0.5  # v sekundách

# Funkcia na blikanie LED v samostatnom vlákne
def blink_thread():
    global led_on, interval
    while True:
        if led_on:
            led.value(1)
            print("LED stav: ZAP")
            time.sleep(interval)
            led.value(0)
            print("LED stav: VYP")
            time.sleep(interval)
        else:
            led.value(0)
            print("LED stav: VYP")
            time.sleep(0.2)

# Spusti blikanie vo vlákne
_thread.start_new_thread(blink_thread, ())

# Pripojenie na WiFi (zmeň SSID a heslo)
ssid = "ASUS_ST"
password = "Siemens2025"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

print("Pripájam na WiFi...")
while not wlan.isconnected():
    time.sleep(0.5)
print("WiFi pripojené:", wlan.ifconfig())

# Web server
html = """
<!DOCTYPE html>
<html>
<head><title>Pico LED Web</title></head>
<body>
<h2>Pico LED Webserver</h2>
<p>LED je: <b>{status}</b></p>
<form method='GET'>
  <button name='led' value='on' type='submit'>Zapnúť LED</button>
  <button name='led' value='off' type='submit'>Vypnúť LED</button><br><br>
  Interval blikania (s): <input name='interval' type='number' step='0.1' min='0.1' value='{interval}'>
  <button type='submit'>Nastaviť</button>
</form>
</body></html>
"""

addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)
print('Web server beží na http://%s/' % wlan.ifconfig()[0])
print('Otvorte túto adresu v prehliadači v rovnakej WiFi sieti.')

while True:
    cl, addr = s.accept()
    print('Klient:', addr)
    request = cl.recv(1024).decode()
    # Spracuj požiadavku
    if 'GET' in request:
        if 'led=on' in request:
            led_on = True
        elif 'led=off' in request:
            led_on = False
            led.value(0)  # Okamžite vypni LED
        import re
        m = re.search(r'interval=([0-9.]+)', request)
        if m:
            try:
                interval = max(0.1, float(m.group(1)))
            except:
                pass
    response = html.format(status="ZAP" if led_on else "VYP", interval=interval)
    cl.send(b'HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    cl.send(response.encode())
    cl.close()
