# Raspberry Pi Pico W - Webserver s onboard teplotou (MicroPython, bez špeciálnych knižníc)
import network
import socket
import time
import _thread
from machine import Pin, ADC

# Funkcia na čítanie teploty z onboard senzora (ADC4)
def read_onboard_temp():
    sensor_temp = ADC(4)
    reading = sensor_temp.read_u16()  # 16-bit hodnota
    voltage = reading * 3.3 / 65535   # prepočet na napätie
    temperature = 27 - (voltage - 0.706) / 0.001721  # podľa datasheetu
    return temperature

# LED pre kontrolu
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
            time.sleep(interval)
            led.value(0)
            time.sleep(interval)
        else:
            led.value(0)
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

# --- HASHOVANIE HESLA BEZ ŠPECIÁLNYCH MODULOV ---
def hash_password(password):
    # fallback: jednoduchý "hash" cez base64 (nie bezpečné, ale MicroPython nemá hashlib)
    b = password.encode()
    s = 0
    for c in b:
        s = (s * 31 + c) % 1000000007
    return str(s)

LOGIN_USER = "admin"
LOGIN_PASS_HASH = hash_password("tajneheslo123")

# Web server s teplotou a prihlasovaním
html_login = """
<!DOCTYPE html>
<html>
<head><title>Login</title></head>
<body>
<h2>Pico Webserver - Prihlásenie</h2>
<form method='POST'>
  Meno: <input name='user' type='text'><br>
  Heslo: <input name='pass' type='password'><br>
  <button type='submit'>Prihlásiť</button>
</form>
{msg}
</body></html>
"""

html_main = """
<!DOCTYPE html>
<html>
<head>
<title>Pico Teplota</title>
<meta http-equiv='refresh' content='2'>
</head>
<body>
<h2>Pico Webserver - Teplota</h2>
<p>LED je: <b>{status}</b></p>
<p>Onboard teplota: <b>{temp:.2f} °C</b></p>
<form method='GET'>
  <button name='led' value='on' type='submit'>Zapnúť LED</button>
  <button name='led' value='off' type='submit'>Vypnúť LED</button><br><br>
  Interval blikania (s): <input name='interval' type='number' step='0.1' min='0.1' value='{interval}'>
  <button type='submit'>Nastaviť</button>
</form>
<a href='/logout'>Odhlásiť</a>
</body></html>
"""

# Jednoduchá session (len v RAM, nie cookies)
session_active = False

# Oprava: ak port 80 je obsadený, skús port 8080
try:
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
except OSError:
    print('Port 80 je obsadený, skúšam port 8080...')
    addr = socket.getaddrinfo('0.0.0.0', 8080)[0][-1]
    s = socket.socket()
    s.bind(addr)
s.listen(1)
print('Web server beží na http://%s:%s/' % (wlan.ifconfig()[0], addr[1]))
print('Otvorte túto adresu v prehliadači v rovnakej WiFi sieti.')

while True:
    cl, addr = s.accept()
    print('Klient:', addr)
    request = cl.recv(1024).decode()
    # Prihlasovanie
    if not session_active:
        if 'POST' in request:
            # Získaj meno a heslo z tela požiadavky
            body = request.split('\r\n\r\n', 1)[-1]
            # Parsovanie POST dát bez ure
            def get_val(key):
                for pair in body.split('&'):
                    if pair.startswith(key+'='):
                        return pair[len(key)+1:].replace('+', ' ')
                return ''
            user = get_val('user')
            passwd = get_val('pass')
            if user == LOGIN_USER and hash_password(passwd) == LOGIN_PASS_HASH:
                session_active = True
                response = "HTTP/1.0 303 See Other\r\nLocation: /\r\n\r\n"
                cl.send(response.encode())
                cl.close()
                continue
            else:
                msg = '<p style="color:red">Nesprávne meno alebo heslo!</p>'
                response = html_login.format(msg=msg)
                cl.send(b'HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
                cl.send(response.encode())
                cl.close()
                continue
        else:
            response = html_login.format(msg='')
            cl.send(b'HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
            cl.send(response.encode())
            cl.close()
            continue
    if '/logout' in request:
        session_active = False
        response = "HTTP/1.0 303 See Other\r\nLocation: /\r\n\r\n"
        cl.send(response.encode())
        cl.close()
        continue
    # Spracuj požiadavku
    if 'GET' in request:
        if 'led=on' in request:
            led_on = True
        elif 'led=off' in request:
            led_on = False
            led.value(0)
        import re
        m = re.search(r'interval=([0-9.]+)', request)
        if m:
            try:
                interval = max(0.1, float(m.group(1)))
            except:
                pass
    temp = read_onboard_temp()
    response = html_main.format(status="ZAP" if led_on else "VYP", interval=interval, temp=temp)
    cl.send(b'HTTP/1.0 200 OK\r\nContent-type: text/html; charset=utf-8\r\n\r\n')
    cl.send(response.encode('utf-8'))
    cl.close()
