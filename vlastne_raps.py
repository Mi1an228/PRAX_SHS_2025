# Raspberry Pi Pico W - Webserver: LED blikanie podľa teploty + prihlasovanie (MicroPython)
import network
import socket
import time
from machine import Pin, ADC

# --- HASHOVANIE HESLA BEZ ŠPECIÁLNYCH MODULOV ---
def hash_password(password):
    b = password.encode()
    s = 0
    for c in b:
        s = (s * 31 + c) % 1000000007
    return str(s)

LOGIN_USER = "admin"
LOGIN_PASS_HASH = hash_password("tajneheslo123")

html_login = """
<!DOCTYPE html>
<html>
<head><title>Login</title></head>
<body>
<h2>Pico LED Teplota - Prihlásenie</h2>
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
<title>Pico LED Teplota</title>
<meta http-equiv='refresh' content='2'>
</head>
<body>
<h2>Pico LED Teplota</h2>
<p>Teplota: <b>{temp:.2f} °C</b></p>
<p>LED bliká podľa teploty (vyššia = rýchlejšie)</p>
<form method='POST' action='/logout'><button type='submit'>Odhlásiť</button></form>
</body></html>
"""

# WiFi pripojenie (zmeň podľa seba)
ssid = "ASUS_ST"
password = "Siemens2025"
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)
print("Pripájam na WiFi...")
while not wlan.isconnected():
    time.sleep(0.5)
print("WiFi pripojené:", wlan.ifconfig())

# LED a teplomer
led = Pin(25, Pin.OUT)
sensor_temp = ADC(4)

# Výpočet teploty z ADC (Pico špecifické)
def get_temp():
    reading = sensor_temp.read_u16() * 3.3 / 65535
    temp_c = 27 - (reading - 0.706) / 0.001721
    return temp_c

# --- Webserver s prihlasovaním a LED blikaním podľa teploty ---
# Porty na skúšanie
ports = [80, 8080, 8081]
s = None
addr = None
for p in ports:
    try:
        addr = socket.getaddrinfo('0.0.0.0', p)[0][-1]
        s = socket.socket()
        s.bind(addr)
        break
    except OSError:
        continue
if s is None or addr is None:
    print('Chyba: Nepodarilo sa otvoriť žiadny port!')
    import sys
    sys.exit()
s.listen(1)
print('Web server beží na http://%s:%s/' % (wlan.ifconfig()[0], addr[1]))
print('Otvorte túto adresu v prehliadači v rovnakej WiFi sieti.')

# Hlavná slučka: webserver + LED blikanie v jednom cykle
session_active = False
last_blink = 0
led_on = False

while True:
    # LED blikanie podľa teploty (len ak prihlásený)
    temp = get_temp()
    interval = max(0.1, min(2.0, 2.5 - (temp-20)*0.1))
    now = int(time.time() * 1000)  # milisekundy
    if session_active:
        if not led_on and (now - last_blink) > interval*1000:
            led.value(1)
            led_on = True
            last_blink = now
        elif led_on and (now - last_blink) > 100:
            led.value(0)
            led_on = False
            last_blink = now
    else:
        led.value(0)
        led_on = False
    # Webserver
    s.settimeout(0.05)
    try:
        cl, addr = s.accept()
    except OSError:
        continue
    try:
        request = cl.recv(1024).decode()
    except:
        cl.close()
        continue
    # Prihlasovanie
    if not session_active:
        if 'POST' in request:
            body = request.split('\r\n\r\n', 1)[-1]
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
                cl.send(b'HTTP/1.0 200 OK\r\nContent-type: text/html; charset=utf-8\r\n\r\n')
                cl.send(response.encode('utf-8'))
                cl.close()
                continue
        else:
            response = html_login.format(msg='')
            cl.send(b'HTTP/1.0 200 OK\r\nContent-type: text/html; charset=utf-8\r\n\r\n')
            cl.send(response.encode('utf-8'))
            cl.close()
            continue
    if '/logout' in request:
        session_active = False
        response = "HTTP/1.0 303 See Other\r\nLocation: /\r\n\r\n"
        cl.send(response.encode())
        cl.close()
        continue
    # Hlavná stránka
    response = html_main.format(temp=temp)
    cl.send(b'HTTP/1.0 200 OK\r\nContent-type: text/html; charset=utf-8\r\n\r\n')
    cl.send(response.encode('utf-8'))
    cl.close()
