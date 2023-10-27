from bin.miniterm import key_description
from odoo import api, models, registry, SUPERUSER_ID
from odoo import tools
from odoo.tools.safe_eval import safe_eval
from odoo.tools.misc import split_every
import threading
from binascii import Error as binascii_error
import re

_image_dataurl = re.compile(r'(data:image/[a-z]+?);base64,([a-z0-9+/\n]{3,}=*)\n*([\'"])(?: data-filename="([^"]*)")?', re.I)

import logging

_logger = logging.getLogger(__name__)

class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self, auto_commit=False):
        #OVERRIDE-popsolutions - DE ./odoo/addons/mail/wizard/mail_compose_message.py
        #OVERRIDE-popsolutions - as linhas modificadas estão com #OVERRIDE-popsolutions
        #OVERRIDE-popsolutions - Este override existe apenas para modificar a linha que faz mail_auto_delete fica TRUE

        """ Process the wizard content and proceed with sending the related
            email(s), rendering any template patterns on the fly if needed. """
        notif_layout = self._context.get('custom_layout')
        # Several custom layouts make use of the model description at rendering, e.g. in the
        # 'View <document>' button. Some models are used for different business concepts, such as
        # 'purchase.order' which is used for a RFQ and and PO. To avoid confusion, we must use a
        # different wording depending on the state of the object.
        # Therefore, we can set the description in the context from the beginning to avoid falling
        # back on the regular display_name retrieved in '_notify_prepare_template_context'.
        model_description = self._context.get('model_description')
        for wizard in self:
            # Duplicate attachments linked to the email.template.
            # Indeed, basic mail.compose.message wizard duplicates attachments in mass
            # mailing mode. But in 'single post' mode, attachments of an email template
            # also have to be duplicated to avoid changing their ownership.
            if wizard.attachment_ids and wizard.composition_mode != 'mass_mail' and wizard.template_id:
                new_attachment_ids = []
                for attachment in wizard.attachment_ids:
                    if attachment in wizard.template_id.attachment_ids:
                        new_attachment_ids.append(attachment.copy({'res_model': 'mail.compose.message', 'res_id': wizard.id}).id)
                    else:
                        new_attachment_ids.append(attachment.id)
                wizard.write({'attachment_ids': [(6, 0, new_attachment_ids)]})

            # Mass Mailing
            mass_mode = wizard.composition_mode in ('mass_mail', 'mass_post')

            Mail = self.env['mail.mail']
            ActiveModel = self.env[wizard.model] if wizard.model and hasattr(self.env[wizard.model], 'message_post') else self.env['mail.thread']
            if wizard.composition_mode == 'mass_post':
                # do not send emails directly but use the queue instead
                # add context key to avoid subscribing the author
                ActiveModel = ActiveModel.with_context(mail_notify_force_send=False, mail_create_nosubscribe=True)
            # wizard works in batch mode: [res_id] or active_ids or active_domain
            if mass_mode and wizard.use_active_domain and wizard.model:
                res_ids = self.env[wizard.model].search(safe_eval(wizard.active_domain)).ids
            elif mass_mode and wizard.model and self._context.get('active_ids'):
                res_ids = self._context['active_ids']
            else:
                res_ids = [wizard.res_id]

            batch_size = int(self.env['ir.config_parameter'].sudo().get_param('mail.batch_size')) or self._batch_size
            sliced_res_ids = [res_ids[i:i + batch_size] for i in range(0, len(res_ids), batch_size)]

            if wizard.composition_mode == 'mass_mail' or wizard.is_log or (wizard.composition_mode == 'mass_post' and not wizard.notify):  # log a note: subtype is False
                subtype_id = False
            elif wizard.subtype_id:
                subtype_id = wizard.subtype_id.id
            else:
                subtype_id = self.env['ir.model.data'].xmlid_to_res_id('mail.mt_comment')

            for res_ids in sliced_res_ids:
                batch_mails = Mail
                all_mail_values = wizard.get_mail_values(res_ids)
                for res_id, mail_values in all_mail_values.items():
                    if wizard.composition_mode == 'mass_mail':
                        batch_mails |= Mail.create(mail_values)
                    else:
                        post_params = dict(
                            message_type=wizard.message_type,
                            subtype_id=subtype_id,
                            notif_layout=notif_layout,
                            add_sign=not bool(wizard.template_id),
                            #mail_auto_delete=wizard.template_id.auto_delete if wizard.template_id else True, #OVERRIDE-popsolutions - Este override existe apenas para modificar esta linha (Substituída pela linha mais abaixo) para fazer com que autodelete obedeça o que foi configurado no modelo de email
                            mail_auto_delete=wizard.template_id.auto_delete, #OVERRIDE-popsolutions - Esta linha substitui a linha anterior
                            model_description=model_description,
                            **mail_values)
                        if ActiveModel._name == 'mail.thread' and wizard.model:
                            post_params['model'] = wizard.model
                        ActiveModel.browse(res_id).message_post(**post_params)

                if wizard.composition_mode == 'mass_mail':
                    batch_mails.send(auto_commit=auto_commit)

class Message(models.Model):
    _inherit = "mail.message"

    @api.multi
    def _notify_compute_recipients(self, record, msg_vals):
        #OVERRIDE-popsolutions - /home/mateus/OdooDev/odoo/addons/mail/models/mail_message.py
        #OVERRIDE-popsolutions - as linhas modificadas estão com #OVERRIDE-popsolutions
        """ Compute recipients to notify based on subtype and followers. This
        method returns data structured as expected for ``_notify_recipients``. """
        msg_sudo = self.sudo()

        pids = [x[1] for x in msg_vals.get('partner_ids')] if 'partner_ids' in msg_vals else msg_sudo.partner_ids.ids
        cids = [x[1] for x in msg_vals.get('channel_ids')] if 'channel_ids' in msg_vals else msg_sudo.channel_ids.ids
        subtype_id = msg_vals.get('subtype_id') if 'subtype_id' in msg_vals else msg_sudo.subtype_id.id

        recipient_data = {
            'partners': [],
            'channels': [],
        }

        # res = self.env['mail.followers']._get_recipient_data(record, subtype_id, pids, cids) #OVERRIDE-popsolutions - Linha substituída pela linha abaixo para que não envie email para seguidiores, apenas para invoice send
        res = self.env['mail.followers']._get_recipient_data(None, subtype_id, pids, cids) #OVERRIDE-popsolutions - Substitui a linha acima conforme explicação na linha acima
        author_id = msg_vals.get('author_id') or self.author_id.id if res else False
        for pid, cid, active, pshare, ctype, notif, groups in res:
            if pid and pid == author_id and not self.env.context.get('mail_notify_author'):  # do not notify the author of its own messages
                continue
            if pid:
                if active is False:
                    # avoid to notify inactive partner by email (odoobot)
                    continue
                pdata = {'id': pid, 'active': active, 'share': pshare, 'groups': groups}
                if notif == 'inbox':
                    recipient_data['partners'].append(dict(pdata, notif=notif, type='user'))
                else:
                    if not pshare and notif:  # has an user and is not shared, is therefore user
                        recipient_data['partners'].append(dict(pdata, notif='email', type='user'))
                    elif pshare and notif:  # has an user but is shared, is therefore portal
                        recipient_data['partners'].append(dict(pdata, notif='email', type='portal'))
                    else:  # has no user, is therefore customer
                        recipient_data['partners'].append(dict(pdata, notif='email', type='customer'))
            elif cid:
                recipient_data['channels'].append({'id': cid, 'notif': notif, 'type': ctype})
        return recipient_data


class MailTemplate(models.Model):
    _inherit = "mail.template"

class IrMailServer(models.Model):
    _inherit = "ir.mail_server"

    def send_email(self, message, mail_server_id=None, smtp_server=None,
                   smtp_port=None, smtp_user=None, smtp_password=None,
                   smtp_encryption=None, smtp_debug=False, smtp_session=None):
        #OVERRIDE-popsolutions - ./odoo/custom-addons/riviera/social/mail_tracking/models/ir_mail_server.py
        #OVERRIDE-popsolutions - Override apenas para acrescentar no log o email/fatura enviado.

        def alterKey(key: str, newValue: str):
            #Altera um valor em message._headers
            i = 0
            key = key.upper()

            while i < len(message._headers):
                val = message._headers[i]

                if str(val[0]).upper() == key:
                    message._headers[i] = (val[0], newValue)
                    break

                i += 1

        def removeNameEmail():
            #task:336 - Remover o nome que acompanha o e-mail. Por exemplo, se estiver:
            #  To:'"Pedro"<pedro@gmail.com>'
            # deverá ficar apenas: '<pedro@gmail.com>'
            i = 0
            while i < len(message._headers):
                val = message._headers[i]

                if str(val[0]).upper() == 'TO':
                    message._headers[i] = (val[0], val[1].split('<')[1].split('>')[0])
                    break

                i += 1

        removeNameEmail();
        alterKey('Reply-To', 'dcr@rivierasl.com.br')

        message_id = super(IrMailServer, self).send_email(message, mail_server_id, smtp_server,
                   smtp_port, smtp_user, smtp_password, smtp_encryption, smtp_debug, smtp_session)

        try:
            def getKey(key: str):
                key = key.upper()

                for val in message._headers:
                    if str(val[0]).upper() == key:
                        return val[1]

            email_to = getKey('to')
            invoice_id = getKey('X-Odoo-Objects')
            invoice_id = ''.join(filter(str.isdigit, invoice_id or '')) #Extrair apenas os dígitos

            _logger.info('### envio email/fatura:' + email_to + '/' + invoice_id)
        except:
            pass

        return message_id

