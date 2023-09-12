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


class MailMail(models.Model):
    _inherit = 'mail.mail'
    #
    # @api.multi
    # def _send(self, auto_commit=False, raise_exception=False, smtp_session=None):
    #     IrMailServer = self.env['ir.mail_server']
    #     IrAttachment = self.env['ir.attachment']
    #     for mail_id in self.ids:
    #         success_pids = []
    #         failure_type = None
    #         processing_pid = None
    #         mail = None
    #         try:
    #             mail = self.browse(mail_id)
    #             if mail.state != 'outgoing':
    #                 if mail.state != 'exception' and mail.auto_delete:
    #                     mail.sudo().unlink()
    #                 continue
    #
    #             # remove attachments if user send the link with the access_token
    #             body = mail.body_html or ''
    #             attachments = mail.attachment_ids
    #             for link in re.findall(r'/web/(?:content|image)/([0-9]+)', body):
    #                 attachments = attachments - IrAttachment.browse(int(link))
    #
    #             # load attachment binary data with a separate read(), as prefetching all
    #             # `datas` (binary field) could bloat the browse cache, triggerring
    #             # soft/hard mem limits with temporary data.
    #             attachments = [(a['datas_fname'], base64.b64decode(a['datas']), a['mimetype'])
    #                            for a in attachments.sudo().read(['datas_fname', 'datas', 'mimetype']) if a['datas'] is not False]
    #
    #             # specific behavior to customize the send email for notified partners
    #             email_list = []
    #             email_list.append(mail._send_prepare_values())
    #
    #             # if mail.email_to:
    #             #     email_list.append(mail._send_prepare_values())
    #             # for partner in mail.recipient_ids:
    #             #     values = mail._send_prepare_values(partner=partner)
    #             #     values['partner_id'] = partner
    #             #     email_list.append(values)
    #
    #             # headers
    #             headers = {}
    #             ICP = self.env['ir.config_parameter'].sudo()
    #             bounce_alias = ICP.get_param("mail.bounce.alias")
    #             catchall_domain = ICP.get_param("mail.catchall.domain")
    #             if bounce_alias and catchall_domain:
    #                 if mail.model and mail.res_id:
    #                     headers['Return-Path'] = '%s+%d-%s-%d@%s' % (bounce_alias, mail.id, mail.model, mail.res_id, catchall_domain)
    #                 else:
    #                     headers['Return-Path'] = '%s+%d@%s' % (bounce_alias, mail.id, catchall_domain)
    #             if mail.headers:
    #                 try:
    #                     headers.update(safe_eval(mail.headers))
    #                 except Exception:
    #                     pass
    #
    #             # Writing on the mail object may fail (e.g. lock on user) which
    #             # would trigger a rollback *after* actually sending the email.
    #             # To avoid sending twice the same email, provoke the failure earlier
    #             mail.write({
    #                 'state': 'exception',
    #                 'failure_reason': _('Error without exception. Probably due do sending an email without computed recipients.'),
    #             })
    #             # Update notification in a transient exception state to avoid concurrent
    #             # update in case an email bounces while sending all emails related to current
    #             # mail record.
    #             notifs = self.env['mail.notification'].search([
    #                 ('is_email', '=', True),
    #                 ('mail_id', 'in', mail.ids),
    #                 ('email_status', 'not in', ('sent', 'canceled'))
    #             ])
    #             if notifs:
    #                 notif_msg = _('Error without exception. Probably due do concurrent access update of notification records. Please see with an administrator.')
    #                 notifs.sudo().write({
    #                     'email_status': 'exception',
    #                     'failure_type': 'UNKNOWN',
    #                     'failure_reason': notif_msg,
    #                 })
    #
    #             # build an RFC2822 email.message.Message object and send it without queuing
    #             res = None
    #             for email in email_list:
    #                 msg = IrMailServer.build_email(
    #                     email_from=mail.email_from,
    #                     email_to=email.get('email_to'),
    #                     subject=mail.subject,
    #                     body=email.get('body'),
    #                     body_alternative=email.get('body_alternative'),
    #                     email_cc=tools.email_split(mail.email_cc),
    #                     reply_to=mail.reply_to,
    #                     attachments=attachments,
    #                     message_id=mail.message_id,
    #                     references=mail.references,
    #                     object_id=mail.res_id and ('%s-%s' % (mail.res_id, mail.model)),
    #                     subtype='html',
    #                     subtype_alternative='plain',
    #                     headers=headers)
    #                 processing_pid = email.pop("partner_id", None)
    #                 try:
    #                     res = IrMailServer.send_email(
    #                         msg, mail_server_id=mail.mail_server_id.id, smtp_session=smtp_session)
    #                     if processing_pid:
    #                         success_pids.append(processing_pid)
    #                     processing_pid = None
    #                 except AssertionError as error:
    #                     if str(error) == IrMailServer.NO_VALID_RECIPIENT:
    #                         failure_type = "RECIPIENT"
    #                         # No valid recipient found for this particular
    #                         # mail item -> ignore error to avoid blocking
    #                         # delivery to next recipients, if any. If this is
    #                         # the only recipient, the mail will show as failed.
    #                         _logger.info("Ignoring invalid recipients for mail.mail %s: %s",
    #                                      mail.message_id, email.get('email_to'))
    #                     else:
    #                         raise
    #             if res:  # mail has been sent at least once, no major exception occured
    #                 mail.write({'state': 'sent', 'message_id': res, 'failure_reason': False})
    #                 _logger.info('Mail with ID %r and Message-Id %r successfully sent', mail.id, mail.message_id)
    #                 # /!\ can't use mail.state here, as mail.refresh() will cause an error
    #                 # see revid:odo@openerp.com-20120622152536-42b2s28lvdv3odyr in 6.1
    #             mail._postprocess_sent_message(success_pids=success_pids, failure_type=failure_type)
    #         except MemoryError:
    #             # prevent catching transient MemoryErrors, bubble up to notify user or abort cron job
    #             # instead of marking the mail as failed
    #             _logger.exception(
    #                 'MemoryError while processing mail with ID %r and Msg-Id %r. Consider raising the --limit-memory-hard startup option',
    #                 mail.id, mail.message_id)
    #             # mail status will stay on ongoing since transaction will be rollback
    #             raise
    #         except (psycopg2.Error, smtplib.SMTPServerDisconnected):
    #             # If an error with the database or SMTP session occurs, chances are that the cursor
    #             # or SMTP session are unusable, causing further errors when trying to save the state.
    #             _logger.exception(
    #                 'Exception while processing mail with ID %r and Msg-Id %r.',
    #                 mail.id, mail.message_id)
    #             raise
    #         except Exception as e:
    #             failure_reason = tools.ustr(e)
    #             _logger.exception('failed sending mail (id: %s) due to %s', mail.id, failure_reason)
    #             mail.write({'state': 'exception', 'failure_reason': failure_reason})
    #             mail._postprocess_sent_message(success_pids=success_pids, failure_reason=failure_reason, failure_type='UNKNOWN')
    #             if raise_exception:
    #                 if isinstance(e, (AssertionError, UnicodeEncodeError)):
    #                     if isinstance(e, UnicodeEncodeError):
    #                         value = "Invalid text: %s" % e.object
    #                     else:
    #                         # get the args of the original error, wrap into a value and throw a MailDeliveryException
    #                         # that is an except_orm, with name and value as arguments
    #                         value = '. '.join(e.args)
    #                     raise MailDeliveryException(_("Mail Delivery Failed"), value)
    #                 raise
    #
    #         if auto_commit is True:
    #             self._cr.commit()
    #     return True
    #
    # @api.multi
    # def _send_prepare_values(self, partner=None):
    #     """Return a dictionary for specific email values, depending on a
    #     partner, or generic to the whole recipients given by mail.email_to.
    #
    #         :param Model partner: specific recipient partner
    #     """
    #     self.ensure_one()
    #     body = self._send_prepare_body()
    #     body_alternative = tools.html2plaintext(body)
    #
    #     email_to = '_send_prepare_values@gmail.com'
    #
    #     res = {
    #         'body': body,
    #         'body_alternative': body_alternative #,
    #         # 'email_to': 'email_to_mateus@gmail.com',
    #     }
    #     return res


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self, auto_commit=False):
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
                            mail_auto_delete=wizard.template_id.auto_delete,
                            model_description=model_description,
                            **mail_values)
                        if ActiveModel._name == 'mail.thread' and wizard.model:
                            post_params['model'] = wizard.model
                        ActiveModel.browse(res_id).message_post(**post_params)

                if wizard.composition_mode == 'mass_mail':
                    batch_mails.send(auto_commit=auto_commit)

class Partner(models.Model):
    _inherit = "res.partner"
    @api.model
    def _notify(self, message, rdata, record, force_send=False, send_after_commit=True, model_description=False, mail_auto_delete=True):
        # OVERRIDE from /odoo/addons/mail/models/res_partner.py
        """ Method to send email linked to notified messages. The recipients are
        the recordset on which this method is called.

        :param message: mail.message record to notify;
        :param rdata: recipient data (see mail.message _notify);
        :param record: optional record on which the message was posted;
        :param force_send: tells whether to send notification emails within the
          current transaction or to use the email queue;
        :param send_after_commit: if force_send, tells whether to send emails after
          the transaction has been committed using a post-commit hook;
        :param model_description: optional data used in notification process (see
          notification templates);
        :param mail_auto_delete: delete notification emails once sent;
        """
        if not rdata:
            return True

        base_template_ctx = self._notify_prepare_template_context(message, record, model_description=model_description)
        template_xmlid = message.layout if message.layout else 'mail.message_notification_email'
        try:
            base_template = self.env.ref(template_xmlid, raise_if_not_found=True).with_context(lang=base_template_ctx['lang'])
        except ValueError:
            _logger.warning('QWeb template %s not found when sending notification emails. Sending without layouting.' % (template_xmlid))
            base_template = False

        # prepare notification mail values
        base_mail_values = {
            'mail_message_id': message.id,
            'mail_server_id': message.mail_server_id.id,
            'auto_delete': mail_auto_delete,
            # due to ir.rule, user have no right to access parent message if message is not published
            'references': message.parent_id.sudo().message_id if message.parent_id else False,
        }
        if record:
            base_mail_values.update(self.env['mail.thread']._notify_specific_email_values_on_records(message, records=record))

        # classify recipients: actions / no action
        recipients = self.env['mail.thread']._notify_classify_recipients_on_records(message, rdata, records=record)

        Mail = self.env['mail.mail'].sudo()
        emails = self.env['mail.mail'].sudo()
        email_pids = set()
        recipients_nbr, recipients_max = 0, 50
        for group_tpl_values in [group for group in recipients.values() if group['recipients']]:
            # generate notification email content
            template_ctx = {**base_template_ctx, **group_tpl_values}
            mail_body = base_template.render(template_ctx, engine='ir.qweb', minimal_qcontext=True) if base_template else message.body
            mail_body = self.env['mail.thread']._replace_local_links(mail_body)
            mail_subject = message.subject or (message.record_name and 'Re: %s' % message.record_name)

            # send email
            for email_chunk in split_every(50, group_tpl_values['recipients']):
                recipient_values = self.env['mail.thread']._notify_email_recipients_on_records(message, email_chunk, records=record)
                create_values = {
                    'body_html': mail_body,
                    'subject': mail_subject,
                }
                create_values.update(base_mail_values)
                create_values.update(recipient_values)
                recipient_ids = [r[1] for r in create_values.get('recipient_ids', [])]
                email = Mail.create(create_values)

                if email and recipient_ids:
                    notifications = self.env['mail.notification'].sudo().search([
                        ('mail_message_id', '=', email.mail_message_id.id),
                        ('res_partner_id', 'in', list(recipient_ids))
                    ])
                    notifications.write({
                        'is_email': True,
                        'mail_id': email.id,
                        'is_read': True,  # handle by email discards Inbox notification
                        'email_status': 'ready',
                    })

                emails |= email
                email_pids.update(recipient_ids)

        # NOTE:
        #   1. for more than 50 followers, use the queue system
        #   2. do not send emails immediately if the registry is not loaded,
        #      to prevent sending email during a simple update of the database
        #      using the command-line.
        test_mode = getattr(threading.currentThread(), 'testing', False)
        if force_send and len(emails) < recipients_max and \
                (not self.pool._init or test_mode):
            email_ids = emails.ids
            dbname = self.env.cr.dbname
            _context = self._context

            def send_notifications():
                db_registry = registry(dbname)
                with api.Environment.manage(), db_registry.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, _context)
                    env['mail.mail'].browse(email_ids).send()

            # unless asked specifically, send emails after the transaction to
            # avoid side effects due to emails being sent while the transaction fails
            if not test_mode and send_after_commit:
                self._cr.after('commit', send_notifications)
            else:
                emails.send()

        return True

class Message(models.Model):
    _inherit = "mail.message"

    @api.multi
    def _notify_compute_recipients(self, record, msg_vals):
        #OVERRIDE /home/mateus/OdooDev/odoo/addons/mail/models/mail_message.py
        """ Compute recipients to notify based on subtype and followers. This
        method returns data structured as expected for ``_notify_recipients``. """
        # recipient_data = {
        #     'partners': [],
        #     'channels': [],
        # }
        #
        # return recipient_data


        msg_sudo = self.sudo()

        pids = [x[1] for x in msg_vals.get('partner_ids')] if 'partner_ids' in msg_vals else msg_sudo.partner_ids.ids
        cids = [x[1] for x in msg_vals.get('channel_ids')] if 'channel_ids' in msg_vals else msg_sudo.channel_ids.ids
        subtype_id = msg_vals.get('subtype_id') if 'subtype_id' in msg_vals else msg_sudo.subtype_id.id

        recipient_data = {
            'partners': [],
            'channels': [],
        }
        # res = self.env['mail.followers']._get_recipient_data(record, subtype_id, pids, cids)
        res = self.env['mail.followers']._get_recipient_data(None, subtype_id, pids, cids)
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

    @api.model
    def create(self, values):
        #OVERRIDE ./odoo/addons/mail/models/mail_message.py.create
        # coming from mail.js that does not have pid in its values
        if self.env.context.get('default_starred'):
            self = self.with_context(default_starred_partner_ids=[(4, self.env.user.partner_id.id)])

        if 'email_from' not in values:  # needed to compute reply_to
            values['email_from'] = self._get_default_from()
        if not values.get('message_id'):
            values['message_id'] = self._get_message_id(values)
        if 'reply_to' not in values:
            values['reply_to'] = self._get_reply_to(values)
        if 'record_name' not in values and 'default_record_name' not in self.env.context:
            values['record_name'] = self._get_record_name(values)

        if 'attachment_ids' not in values:
            values.setdefault('attachment_ids', [])

        # extract base64 images
        if 'body' in values:
            Attachments = self.env['ir.attachment']
            data_to_url = {}
            def base64_to_boundary(match):
                key = match.group(2)
                if not data_to_url.get(key):
                    name = match.group(4) if match.group(4) else 'image%s' % len(data_to_url)
                    try:
                        attachment = Attachments.create({
                            'name': name,
                            'datas': match.group(2),
                            'datas_fname': name,
                            'res_model': values.get('model'),
                            'res_id': values.get('res_id'),
                        })
                    except binascii_error:
                        _logger.warning("Impossible to create an attachment out of badly formated base64 embedded image. Image has been removed.")
                        return match.group(3)  # group(3) is the url ending single/double quote matched by the regexp
                    else:
                        attachment.generate_access_token()
                        values['attachment_ids'].append((4, attachment.id))
                        data_to_url[key] = ['/web/image/%s?access_token=%s' % (attachment.id, attachment.access_token), name]
                return '%s%s alt="%s"' % (data_to_url[key][0], match.group(3), data_to_url[key][1])
            values['body'] = _image_dataurl.sub(base64_to_boundary, tools.ustr(values['body']))

        # delegate creation of tracking after the create as sudo to avoid access rights issues
        tracking_values_cmd = values.pop('tracking_value_ids', False)
        message = super(Message, self).create(values)

        if values.get('attachment_ids'):
            message.attachment_ids.check(mode='read')

        if tracking_values_cmd:
            vals_lst = [dict(cmd[2], mail_message_id=message.id) for cmd in tracking_values_cmd if len(cmd) == 3 and cmd[0] == 0]
            other_cmd = [cmd for cmd in tracking_values_cmd if len(cmd) != 3 or cmd[0] != 0]
            if vals_lst:
                self.env['mail.tracking.value'].sudo().create(vals_lst)
            if other_cmd:
                message.sudo().write({'tracking_value_ids': tracking_values_cmd})

        if values.get('model') and values.get('res_id'):
            message._invalidate_documents()

        # message['email_to'] = 'mateus.2006@gmail.com, spawn.2006@gmail.com'
        return message




class MailTemplate(models.Model):
    _inherit = "mail.template"

    @api.multi
    def generate_recipients(self, results, res_ids):
        #OVERRIDE - odoo/addons/mail/models/mail_template.py
        """Generates the recipients of the template. Default values can ben generated
        instead of the template values if requested by template or context.
        Emails (email_to, email_cc) can be transformed into partners if requested
        in the context. """
        self.ensure_one()

        if self.use_default_to or self._context.get('tpl_force_default_to'):
            default_recipients = self.env['mail.thread'].message_get_default_recipients(res_model=self.model, res_ids=res_ids)
            for res_id, recipients in default_recipients.items():
                results[res_id].pop('partner_to', None)
                results[res_id].update(recipients)

        records_company = None
        if self._context.get('tpl_partners_only') and self.model and results and 'company_id' in self.env[self.model]._fields:
            records = self.env[self.model].browse(results.keys()).read(['company_id'])
            records_company = {rec['id']: (rec['company_id'][0] if rec['company_id'] else None) for rec in records}

        for res_id, values in results.items():
            partner_ids = values.get('partner_ids', list())
            if self._context.get('tpl_partners_only'):
                mails = tools.email_split(values.pop('email_to', '')) + tools.email_split(values.pop('email_cc', ''))
                Partner = self.env['res.partner']
                if records_company:
                    Partner = Partner.with_context(default_company_id=records_company[res_id])
                for mail in mails:
                    partner_id = Partner.find_or_create(mail)
                    partner_ids.append(partner_id)
            partner_to = values.pop('partner_to', '')
            if partner_to:
                # placeholders could generate '', 3, 2 due to some empty field values
                tpl_partner_ids = [int(pid) for pid in partner_to.split(',') if pid]
                partner_ids += self.env['res.partner'].sudo().browse(tpl_partner_ids).exists().ids
            results[res_id]['partner_ids'] = partner_ids

        # results[list(results)[1]].update({'email_to': 'ewqewq@fdasf.com'})
        # results[list(results)[0]]['partner_ids'] = [9020]
        return results


class IrMailServer(models.Model):
    _inherit = "ir.mail_server"

    def send_email(self, message, mail_server_id=None, smtp_server=None,
                   smtp_port=None, smtp_user=None, smtp_password=None,
                   smtp_encryption=None, smtp_debug=False, smtp_session=None):
        #./odoo/custom-addons/riviera/social/mail_tracking/models/ir_mail_server.py
        message_id = super(IrMailServer, self).send_email(message, mail_server_id, smtp_server,
                   smtp_port, smtp_user, smtp_password, smtp_encryption, smtp_debug, smtp_session)

        def getKey(key: str):
            key = key.upper()

            for val in message._headers:
                if str(val[0]).upper() == key:
                    return val[1]

        email_to = getKey('to')
        invoice_id = getKey('X-Odoo-Objects')
        invoice_id = ''.join(filter(str.isdigit, invoice_id)) #Extrair apenas os dígitos

        _logger.info('### envio email/fatura:' + email_to + '/' + invoice_id)

        return message_id

