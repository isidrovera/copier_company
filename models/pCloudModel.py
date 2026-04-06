from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import base64
import logging

_logger = logging.getLogger(__name__)


class PCloudConfig(models.Model):
    _name = 'pcloud.config'
    _description = 'pCloud Configuration'

    name = fields.Char(string='Name', required=True)
    client_id = fields.Char(string='Client ID', required=True)
    client_secret = fields.Char(string='Client Secret', required=True)
    access_token = fields.Char(string='Access Token')
    redirect_uri = fields.Char(string='Redirect URI', required=True)
    hostname = fields.Char(string='Hostname')

    def _get_api_url(self):
        self.ensure_one()
        hostname = self.hostname or 'api.pcloud.com'
        if not hostname.startswith('http'):
            hostname = 'https://' + hostname
        return hostname.rstrip('/')

    def get_authorization_url(self):
        self.ensure_one()
        url = "https://my.pcloud.com/oauth2/authorize"
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'state': 'random_state',
        }
        return requests.Request('GET', url, params=params).prepare().url

    def get_access_token(self, code):
        self.ensure_one()
        url = "https://api.pcloud.com/oauth2_token"
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
        }
        try:
            response = requests.get(url, params=params, timeout=30)
            _logger.info('pCloud oauth2_token status: %s body: %s',
                         response.status_code, response.text)
        except requests.exceptions.RequestException as e:
            raise UserError(f"Error de conexión con pCloud: {str(e)}")

        if response.status_code != 200:
            raise UserError(f"pCloud HTTP {response.status_code}: {response.text}")

        data = response.json()
        if data.get('result', 0) != 0:
            raise UserError(f"pCloud error {data.get('result')}: {data.get('error', 'desconocido')}")

        access_token = data.get('access_token')
        if not access_token:
            raise UserError(f"pCloud no devolvió access_token. Respuesta: {data}")

        self.write({
            'access_token': access_token,
            'hostname': self.hostname or 'api.pcloud.com',
        })
        _logger.info('pCloud token guardado correctamente para config ID %s', self.id)

    def create_pcloud_folder(self, folder_name, parent_folder_id=0):
        self.ensure_one()
        if not self.access_token:
            raise UserError("No hay token. Conéctate a pCloud primero.")
        url = f"{self._get_api_url()}/createfolder"
        response = requests.get(url, params={
            'access_token': self.access_token,
            'name': folder_name,
            'folderid': parent_folder_id,
        }, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('result') != 0:
                raise UserError(f"pCloud error: {data.get('error')}")
            return data['metadata']['folderid']
        raise UserError("Error al crear carpeta en pCloud")

    def upload_file_to_pcloud(self, file_path, folder_id):
        self.ensure_one()
        if not self.access_token:
            raise UserError("No hay token. Conéctate a pCloud primero.")
        url = f"{self._get_api_url()}/uploadfile"
        with open(file_path, 'rb') as f:
            response = requests.post(url, params={
                'access_token': self.access_token,
                'folderid': folder_id,
            }, files={'file': f}, timeout=120)
        if response.status_code == 200:
            data = response.json()
            if data.get('result') != 0:
                raise UserError(f"pCloud error: {data.get('error')}")
            return data['metadata'][0]['fileid']
        raise UserError("Error al subir archivo a pCloud")

    def list_pcloud_contents(self, folder_id=0):
        self.ensure_one()
        if not self.access_token:
            raise UserError("No hay token. Conéctate a pCloud primero.")
        url = f"{self._get_api_url()}/listfolder"
        response = requests.get(url, params={
            'access_token': self.access_token,
            'folderid': folder_id,
        }, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('result') != 0:
                raise UserError(f"pCloud error: {data.get('error')}")
            return data['metadata']['contents']
        raise UserError("Error al listar contenido de pCloud")

    def list_pcloud_folders(self, folder_id=0):
        return self.list_pcloud_contents(folder_id)

    def get_pcloud_file_info(self, file_id):
        self.ensure_one()
        if not self.access_token:
            raise UserError("No hay token. Conéctate a pCloud primero.")
        url = f"{self._get_api_url()}/getfilelink"
        response = requests.get(url, params={
            'access_token': self.access_token,
            'fileid': file_id,
        }, timeout=30)
        if response.status_code == 200:
            return response.json()
        raise UserError("Error al obtener info del archivo")

    def download_pcloud_file(self, file_id):
        self.ensure_one()
        if not self.access_token:
            raise UserError("No hay token. Conéctate a pCloud primero.")
        url = f"{self._get_api_url()}/getfilelink"
        response = requests.get(url, params={
            'access_token': self.access_token,
            'fileid': file_id,
        }, timeout=30)
        if response.status_code == 200:
            data = response.json()
            _logger.info('pCloud getfilelink response: %s', data)
            if data.get('result') != 0:
                raise UserError(f"pCloud error: {data.get('error')}")
            hosts = data.get('hosts', [])
            path = data.get('path', '')
            if not hosts or not path:
                raise UserError("pCloud no devolvió hosts/path para descarga")
            download_url = hosts[0] + path
            if not download_url.startswith('http'):
                download_url = 'https://' + download_url
            return download_url
        raise UserError("Error al obtener link de descarga")

    def get_folder_path(self, folder_id):
        self.ensure_one()
        if not self.access_token:
            raise UserError("No hay token. Conéctate a pCloud primero.")
        folder_path = []
        current_id = folder_id
        max_depth = 20
        while current_id != 0 and len(folder_path) < max_depth:
            url = f"{self._get_api_url()}/listfolder"
            try:
                response = requests.get(url, params={
                    'access_token': self.access_token,
                    'folderid': current_id,
                }, timeout=30)
                if response.status_code == 200:
                    folder_info = response.json().get('metadata', {})
                    folder_path.insert(0, {
                        'id': current_id,
                        'name': folder_info.get('name', 'Unknown'),
                        'parentfolderid': folder_info.get('parentfolderid', 0),
                    })
                    current_id = folder_info.get('parentfolderid', 0)
                else:
                    break
            except Exception as e:
                _logger.error('Error getting folder path: %s', str(e))
                break
        return folder_path

    def action_connect_to_pcloud(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self.get_authorization_url(),
            'target': 'new',
        }

    def action_disconnect_from_pcloud(self):
        self.ensure_one()
        self.write({'access_token': False})

    def action_open_explorer(self):
        self.ensure_one()
        if not self.access_token:
            raise UserError('Conéctate a pCloud primero.')
        wizard = self.env['pcloud.explorer'].create({
            'config_id': self.id,
        })
        self.env.cr.flush()
        wizard._load_contents()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pcloud.explorer',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'mode': 'edit'},
        }

    # ─── MÉTODOS RPC PARA EL EXPLORADOR OWL ───────────────────────────────────

    @api.model
    def pcloud_get_config(self):
        """Retorna el config activo con token"""
        config = self.search([('access_token', '!=', False)], limit=1)
        if not config:
            raise UserError('No hay configuración de pCloud con token activo.')
        return {'config_id': config.id, 'name': config.name}

    @api.model
    def pcloud_list_contents(self, folder_id=0):
        """Lista contenido de una carpeta — llamado desde OWL via RPC"""
        config = self.search([('access_token', '!=', False)], limit=1)
        if not config:
            raise UserError('No hay configuración de pCloud activa.')
        items = config.list_pcloud_contents(int(folder_id))
        result = []
        for item in items:
            is_folder = item.get('isfolder', False)
            # Verificar si ya tiene producto creado
            folder_item_id = str(item.get('folderid') if is_folder else item.get('fileid'))
            has_product = False
            if is_folder:
                has_product = self._pcloud_folder_has_product(folder_item_id)
            result.append({
                'id': folder_item_id,
                'name': item.get('name', ''),
                'is_folder': is_folder,
                'size': item.get('size', 0),
                'modified': item.get('modified', ''),
                'has_product': has_product,
            })
        result.sort(key=lambda x: (not x['is_folder'], x['name'].lower()))
        return result

    @api.model
    def _pcloud_folder_has_product(self, folder_id):
        """Verifica si ya existe un producto vinculado a esta carpeta pCloud"""
        # Busca en ir.attachment si hay una URL de pCloud que contenga el código
        # de esta carpeta, vinculada a un product.document
        attachment = self.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'product.template'),
            ('url', '!=', False),
        ], limit=0)
        # Buscamos en product_document por el folder_id guardado en el campo
        # pcloud_folder_id del producto
        product = self.env['product.template'].sudo().search([
            ('pcloud_folder_id', '=', str(folder_id)),
        ], limit=1)
        return bool(product)

    @api.model
    def pcloud_create_folder(self, name, folder_id=0):
        """Crea una carpeta"""
        config = self.search([('access_token', '!=', False)], limit=1)
        if not config:
            raise UserError('No hay configuración de pCloud activa.')
        new_id = config.create_pcloud_folder(name, int(folder_id))
        return {'id': str(new_id), 'name': name}

    @api.model
    def pcloud_delete(self, item_id, is_folder):
        """Elimina archivo o carpeta"""
        config = self.search([('access_token', '!=', False)], limit=1)
        if not config:
            raise UserError('No hay configuración de pCloud activa.')
        endpoint = '/deletefolderrecursive' if is_folder else '/deletefile'
        param_key = 'folderid' if is_folder else 'fileid'
        url = f"{config._get_api_url()}{endpoint}"
        response = requests.get(url, params={
            'access_token': config.access_token,
            param_key: int(item_id),
        }, timeout=30)
        data = response.json()
        if data.get('result') != 0:
            raise UserError(f"pCloud error: {data.get('error', 'desconocido')}")
        return True

    @api.model
    def pcloud_rename(self, item_id, new_name, is_folder):
        """Renombra archivo o carpeta"""
        config = self.search([('access_token', '!=', False)], limit=1)
        if not config:
            raise UserError('No hay configuración de pCloud activa.')
        endpoint = '/renamefolder' if is_folder else '/renamefile'
        param_key = 'folderid' if is_folder else 'fileid'
        url = f"{config._get_api_url()}{endpoint}"
        response = requests.get(url, params={
            'access_token': config.access_token,
            param_key: int(item_id),
            'toname': new_name,
        }, timeout=30)
        data = response.json()
        if data.get('result') != 0:
            raise UserError(f"pCloud error: {data.get('error', 'desconocido')}")
        return True

    @api.model
    def pcloud_upload(self, filename, file_b64, folder_id=0):
        """Sube un archivo codificado en base64"""
        config = self.search([('access_token', '!=', False)], limit=1)
        if not config:
            raise UserError('No hay configuración de pCloud activa.')
        file_content = base64.b64decode(file_b64)
        url = f"{config._get_api_url()}/uploadfile"
        response = requests.post(url, params={
            'access_token': config.access_token,
            'folderid': int(folder_id),
        }, files={'file': (filename, file_content)}, timeout=120)
        data = response.json()
        if data.get('result') != 0:
            raise UserError(f"pCloud error: {data.get('error', 'desconocido')}")
        file_id = str(data['metadata'][0]['fileid'])
        return {'id': file_id, 'name': filename}

    @api.model
    def pcloud_get_share_link(self, folder_id):
        """Obtiene o crea link público permanente de una carpeta"""
        config = self.search([('access_token', '!=', False)], limit=1)
        if not config:
            raise UserError('No hay configuración de pCloud activa.')
        url = f"{config._get_api_url()}/getfolderpublink"
        response = requests.get(url, params={
            'access_token': config.access_token,
            'folderid': int(folder_id),
        }, timeout=30)
        data = response.json()
        if data.get('result') != 0:
            raise UserError(f"pCloud error: {data.get('error', 'desconocido')}")
        code = data.get('code', '')
        return {
            'link': f"https://u.pcloud.link/publink/show?code={code}",
            'code': code,
        }

    @api.model
    def pcloud_delete_share_link(self, code):
        """Elimina un link público por su código"""
        config = self.search([('access_token', '!=', False)], limit=1)
        if not config:
            raise UserError('No hay configuración de pCloud activa.')
        url = f"{config._get_api_url()}/deletepublink"
        response = requests.get(url, params={
            'access_token': config.access_token,
            'code': code,
        }, timeout=30)
        data = response.json()
        if data.get('result') != 0:
            raise UserError(f"pCloud error: {data.get('error', 'desconocido')}")
        return True

    @api.model
    def pcloud_move(self, item_id, target_folder_id, is_folder):
        """Mueve archivo o carpeta a otra carpeta"""
        config = self.search([('access_token', '!=', False)], limit=1)
        if not config:
            raise UserError('No hay configuración de pCloud activa.')
        endpoint = '/renamefolder' if is_folder else '/renamefile'
        param_key = 'folderid' if is_folder else 'fileid'
        url = f"{config._get_api_url()}{endpoint}"
        response = requests.get(url, params={
            'access_token': config.access_token,
            param_key: int(item_id),
            'tofolderid': int(target_folder_id),
        }, timeout=30)
        data = response.json()
        if data.get('result') != 0:
            raise UserError(f"pCloud error: {data.get('error', 'desconocido')}")
        return True

    @api.model
    def pcloud_get_file_download_url(self, file_id):
        """Obtiene URL de descarga directa de un archivo"""
        config = self.search([('access_token', '!=', False)], limit=1)
        if not config:
            raise UserError('No hay configuración de pCloud activa.')
        return config.download_pcloud_file(int(file_id))

    @api.model
    def pcloud_create_products_from_folders(self, folders, price_pen=100.0, price_usd=25.0):
        _logger.info('[pCloud] Creating products from %s folders', len(folders))

        config = self.search([('access_token', '!=', False)], limit=1)
        if not config:
            raise UserError('No hay configuración de pCloud activa.')

        # Pricelists
        pricelist_pen = self.env['product.pricelist'].sudo().search([
            ('currency_id.name', '=', 'PEN'),
        ], limit=1)

        pricelist_usd = self.env['product.pricelist'].sudo().search([
            ('currency_id.name', '=', 'USD'),
        ], limit=1)

        # IGV
        tax_igv = self.env['account.tax'].sudo().search([
            ('name', 'ilike', 'IGV'),
            ('type_tax_use', '=', 'sale'),
            ('amount', '=', 18.0),
        ], limit=1)

        results = []

        for folder in folders:
            folder_id = str(folder.get('id', ''))
            folder_name = folder.get('name', '').strip()

            if not folder_id or not folder_name:
                results.append({
                    'folder_id': folder_id,
                    'folder_name': folder_name,
                    'status': 'error',
                    'message': 'Carpeta inválida',
                    'product_id': None,
                    'product_name': None,
                })
                continue

            product_name = f"Firmware {folder_name}"
            _logger.info('[pCloud] Processing folder: %s -> %s', folder_id, product_name)

            # ─────────────────────────────
            # 1. PRODUCTO (IDEMPOTENTE)
            # ─────────────────────────────
            product = self.env['product.template'].sudo().search([
                ('pcloud_folder_id', '=', folder_id),
            ], limit=1)

            if not product:
                vals = {
                    'name': product_name,
                    'type': 'service',
                    'sale_ok': True,
                    'purchase_ok': False,
                    'list_price': float(price_pen),
                    'pcloud_folder_id': folder_id,
                    'website_published': True,
                }

                if tax_igv:
                    vals['taxes_id'] = [(6, 0, [tax_igv.id])]

                product = self.env['product.template'].sudo().create(vals)
                _logger.info('[pCloud] Product CREATED: %s', product.id)
            else:
                _logger.info('[pCloud] Product EXISTS: %s', product.id)

            # ─────────────────────────────
            # 2. LINK PÚBLICO
            # ─────────────────────────────
            share = config._get_or_create_folder_publink(int(folder_id))
            public_link = share['link']

            # ─────────────────────────────
            # 3. PRECIOS (UPSERT)
            # ─────────────────────────────
            def upsert_pricelist(pricelist, price):
                if not pricelist:
                    return
                item = self.env['product.pricelist.item'].sudo().search([
                    ('pricelist_id', '=', pricelist.id),
                    ('product_tmpl_id', '=', product.id),
                ], limit=1)

                if item:
                    item.write({'fixed_price': float(price)})
                else:
                    self.env['product.pricelist.item'].sudo().create({
                        'pricelist_id': pricelist.id,
                        'product_tmpl_id': product.id,
                        'compute_price': 'fixed',
                        'fixed_price': float(price),
                        'applied_on': '1_product',
                    })

            upsert_pricelist(pricelist_pen, price_pen)
            upsert_pricelist(pricelist_usd, price_usd)

            # ─────────────────────────────
            # 4. ATTACHMENT (SIN DUPLICAR)
            # ─────────────────────────────
            attachment = self.env['ir.attachment'].sudo().search([
                ('res_model', '=', 'product.template'),
                ('res_id', '=', product.id),
                ('url', '=', public_link),
            ], limit=1)

            if not attachment:
                attachment = self.env['ir.attachment'].sudo().create({
                    'name': 'Descarga',
                    'type': 'url',
                    'url': public_link,
                    'res_model': 'product.template',
                    'res_id': product.id,
                    'mimetype': 'text/html',
                })
                _logger.info('[pCloud] Attachment CREATED: %s', attachment.id)
            else:
                _logger.info('[pCloud] Attachment EXISTS: %s', attachment.id)

            # ─────────────────────────────
            # 5. DOCUMENTO (FORZADO SIN DUPLICAR)
            # ─────────────────────────────
            document = self.env['product.document'].sudo().search([
                ('ir_attachment_id', '=', attachment.id),
            ], limit=1)

            if not document:
                document = self.env['product.document'].sudo().create({
                    'ir_attachment_id': attachment.id,
                    'attached_on_sale': 'sale_order',  # ✅ correcto en tu sistema
                    'shown_on_product_page': False,
                })
                _logger.info('[pCloud] Document CREATED')
            else:
                _logger.info('[pCloud] Document EXISTS')

            # 🔥 FORZAR VALOR (evita que otros módulos lo cambien)
            document.sudo().write({
                'attached_on_sale': 'sale_order'
            })

            results.append({
                'folder_id': folder_id,
                'folder_name': folder_name,
                'status': 'ok',
                'message': 'Procesado correctamente',
                'product_id': product.id,
                'product_name': product.name,
            })

        _logger.info('[pCloud] DONE. Total: %s', len(results))
        return results

    def _get_or_create_folder_publink(self, folder_id):
        """
        Obtiene el link público de una carpeta pCloud.
        Si no existe, lo crea.
        """
        self.ensure_one()
        url = f"{self._get_api_url()}/getfolderpublink"
        response = requests.get(url, params={
            'access_token': self.access_token,
            'folderid': folder_id,
        }, timeout=30)
        data = response.json()
        _logger.info('[pCloud] getfolderpublink response for %s: result=%s',
                     folder_id, data.get('result'))

        if data.get('result') == 0:
            code = data.get('code', '')
            return {
                'link': f"https://u.pcloud.link/publink/show?code={code}",
                'code': code,
            }

        # Si no existe el link, intentar crearlo
        _logger.info('[pCloud] No existing publink, creating one for folder %s', folder_id)
        create_url = f"{self._get_api_url()}/createfolderpublink"
        create_response = requests.get(create_url, params={
            'access_token': self.access_token,
            'folderid': folder_id,
        }, timeout=30)
        create_data = create_response.json()
        _logger.info('[pCloud] createfolderpublink response: result=%s',
                     create_data.get('result'))

        if create_data.get('result') == 0:
            code = create_data.get('code', '')
            return {
                'link': f"https://u.pcloud.link/publink/show?code={code}",
                'code': code,
            }

        raise UserError(
            f"No se pudo obtener ni crear el link público para la carpeta {folder_id}. "
            f"Error: {create_data.get('error', 'desconocido')}"
        )

    @api.model
    def pcloud_check_folders_products(self, folder_ids):
        """
        Verifica cuáles carpetas ya tienen producto creado.
        Retorna dict {folder_id: {has_product, product_id, product_name}}
        """
        result = {}
        for fid in folder_ids:
            product = self.env['product.template'].sudo().search([
                ('pcloud_folder_id', '=', str(fid)),
            ], limit=1)
            result[str(fid)] = {
                'has_product': bool(product),
                'product_id': product.id if product else None,
                'product_name': product.name if product else None,
            }
        return result