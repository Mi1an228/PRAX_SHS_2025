# Raspberry Pi Pico W - Morzeovka cez onboard LED + web zadanie mena (MicroPython)
import network
import socket
import time
from machine import Pin

# Morzeovka abeceda
MORSE_CODE = {
    'A': '.-',    'B': '-...',  'C': '-.-.',  'D': '-..',   'E': '.',
    'F': '..-.',  'G': '--.',   'H': '....',  'I': '..',    'J': '.---',
    'K': '-.-',   'L': '.-..',  'M': '--',    'N': '-.',    'O': '---',
    'P': '.--.',  'Q': '--.-',  'R': '.-.',   'S': '...',   'T': '-',
    'U': '..-',   'V': '...-',  'W': '.--',   'X': '-..-',  'Y': '-.--',
    'Z': '--..',  '0': '-----', '1': '.----', '2': '..---', '3': '...--',
    '4': '....-', '5': '.....', '6': '-....', '7': '--...', '8': '---..',
    '9': '----.'
}

led = Pin(25, Pin.OUT)

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

# Morzeovka blikanie
DOT = 0.2  # sekundy
DASH = DOT * 3
GAP = DOT
LETTER_GAP = DOT * 3
WORD_GAP = DOT * 7

# Funkcia na vyblikanie textu v morzeovke
def blink_morse(text):
    for char in text.upper():
        if char == ' ':
            time.sleep(WORD_GAP)
            continue
        code = MORSE_CODE.get(char, '')
        for symbol in code:
            led.value(1)
            if symbol == '.':
                time.sleep(DOT)
            elif symbol == '-':
                time.sleep(DASH)
            led.value(0)
            time.sleep(GAP)
        time.sleep(LETTER_GAP - GAP)

# Web server na zadanie mena
html = """
<!DOCTYPE html>
<html>
<head><title>Morzeovka LED</title></head>
<body>
<h2>Pico Morzeovka LED</h2>
<form method='GET'>
  Meno: <input name='meno' type='text' value='{meno}'>
  <button type='submit'>Vyblikaj</button>
</form>
<p>Aktuálne meno: <b>{meno}</b></p>
</body></html>
"""

# Predvolené meno
meno = "Milan"

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
<h2>Pico Morzeovka LED - Prihlásenie</h2>
<form method='POST'>
  Meno: <input name='user' type='text'><br>
  Heslo: <input name='pass' type='password'><br>
  <button type='submit'>Prihlásiť</button>
</form>
{msg}
</body></html>
"""

html_main = html  # použijeme pôvodný html s formulárom na meno

session_active = False

# Spusti webserver
try:
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
except OSError:
    print('Port 80 je obsadený, skúšam port 8080...')
    try:
        addr = socket.getaddrinfo('0.0.0.0', 8080)[0][-1]
        s = socket.socket()
        s.bind(addr)
    except OSError:
        print('Port 8080 je obsadený, skúšam port 8081...')
        addr = socket.getaddrinfo('0.0.0.0', 8081)[0][-1]
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
    # Získaj meno z GET parametra
    import re
    m = re.search(r'meno=([^& ]+)', request)
    if m:
        meno = m.group(1).replace('+', ' ')
    response = html_main.format(meno=meno)
    cl.send(b'HTTP/1.0 200 OK\r\nContent-type: text/html; charset=utf-8\r\n\r\n')
    cl.send(response.encode('utf-8'))
    cl.close()
    # Vyblikaj meno v morzeovke
    blink_morse(meno)
