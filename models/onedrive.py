from onedrivesdk import (
    AuthenticationProvider,
    OneDriveClient
)
from onedrivesdk.helpers import GetAuthCodeServer
# Configurar las credenciales de la aplicación
client_id = 'su_client_id'
client_secret = 'su_client_secret'
redirect_uri = 'https://copiercompanysac.com/'
scopes=['wl.signin', 'wl.offline_access', 'onedrive.readwrite']

# Obtener el código de autorización
auth_url = GetAuthCodeServer.get_auth_url(client_id, redirect_uri, scopes)
print('Por favor, visite esta URL para obtener el código de autorización: ', auth_url)
code = input('Ingrese el código de autorización: ')

# Autenticarse y obtener una lista de archivos en una carpeta específica
auth = AuthenticationProvider(client_id, client_secret, scopes)
auth.authenticate(code, redirect_uri)
client = OneDriveClient('https://api.onedrive.com/v1.0/', auth, http=None)
archivos = client.item(drive='me', id='carpeta_id').children.get()
for item in archivos:
    print(item.name)


