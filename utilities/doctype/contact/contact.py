# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import webnotes
from webnotes.utils import cstr, extract_email_id

from utilities.transaction_base import TransactionBase
import atom.data
import gdata.data
import gdata.contacts.client
import gdata.contacts.data
from gdata.auth import OAuthSignatureMethod, OAuthToken, OAuthInputParams
import gdata.gauth
import urllib2
import pickle
import gdata
import json




class DocType(TransactionBase):
	def __init__(self, doc, doclist=[]):
		self.doc = doc
		self.doclist = doclist


	def on_update(self):
		webnotes.errprint("in the on_update")
		prepare_data(self.doc)

	def on_communication(self, comm):
		webnotes.errprint("in the on_communication")
		if webnotes.conn.get_value("Profile", extract_email_id(comm.sender), "user_type")=="System User":
			status = "Replied"
		else:
			status = "Open"

		webnotes.conn.set(self.doc, 'status', status)


	def autoname(self):
		webnotes.errprint("in the on_communication")
		# concat first and last name
		self.doc.name = " ".join(filter(None, 
			[cstr(self.doc.fields.get(f)).strip() for f in ["first_name", "last_name"]]))
		
		# concat party name if reqd
		for fieldname in ("customer", "supplier", "sales_partner"):
			if self.doc.fields.get(fieldname):
				self.doc.name = self.doc.name + "-" + cstr(self.doc.fields.get(fieldname)).strip()
				break
		
	def validate(self):
		webnotes.errprint("in the validate")
		self.set_status()
		self.validate_primary_contact()

	def validate_primary_contact(self):
		webnotes.errprint("in the validate primary")
		if self.doc.is_primary_contact == 1:
			if self.doc.customer:
				webnotes.conn.sql("update tabContact set is_primary_contact=0 where customer = '%s'" % (self.doc.customer))
			elif self.doc.supplier:
				webnotes.conn.sql("update tabContact set is_primary_contact=0 where supplier = '%s'" % (self.doc.supplier))	
			elif self.doc.sales_partner:
				webnotes.conn.sql("update tabContact set is_primary_contact=0 where sales_partner = '%s'" % (self.doc.sales_partner))
		else:
			if self.doc.customer:
				if not webnotes.conn.sql("select name from tabContact where is_primary_contact=1 and customer = '%s'" % (self.doc.customer)):
					self.doc.is_primary_contact = 1
			elif self.doc.supplier:
				if not webnotes.conn.sql("select name from tabContact where is_primary_contact=1 and supplier = '%s'" % (self.doc.supplier)):
					self.doc.is_primary_contact = 1
			elif self.doc.sales_partner:
				if not webnotes.conn.sql("select name from tabContact where is_primary_contact=1 and sales_partner = '%s'" % (self.doc.sales_partner)):
					self.doc.is_primary_contact = 1

	def on_trash(self):
		webnotes.conn.sql("""update `tabSupport Ticket` set contact='' where contact=%s""",
			self.doc.name)

def prepare_data(self):
	webnotes.errprint("in the prepare_data")
	""" prepare dict """
	if self.last_name:
		name = self.first_name + ' ' + self.last_name
	else:
		name = self.first_name
	info = {'name': name, 'email':self.email_id, 'phone': self.phone, 'id':self.contct_id}
	webnotes.errprint(self.contct_id)
	if self.contct_id:
		update_contact(info)
	else:
		create_contact_on_google(self, info)

def create_contact_on_google(self, info):
	webnotes.errprint("in the on_commun")

	with open('client.pickle') as pickle_file:
		webnotes.errprint("in the clir")
		client = pickle.load(pickle_file)
		# webnotes.errprint(json.loads(client))
		# client=json.loads(client1)
		# webnotes.errprint(eval(client1))
		# client

	#create contact in google
	new_contact = gdata.contacts.data.ContactEntry()

	# Set the contact's name.
	new_contact.name = gdata.data.Name( given_name=gdata.data.GivenName(text=info['name']), family_name=gdata.data.FamilyName(text=info['name']),
		full_name=gdata.data.FullName(text=info['name']))

	new_contact.content = atom.data.Content(text='Notes')

	# Set the contact's email addresses.
	new_contact.email.append(gdata.data.Email(address=info['email'],  primary='true', rel=gdata.data.WORK_REL, display_name=info['name']))

	# Set the contact's phone numbers.
	new_contact.phone_number.append(gdata.data.PhoneNumber(text=info['phone'], rel=gdata.data.WORK_REL, primay='true'))

	contact_entry = client.CreateContact(new_contact)
	webnotes.errprint("Contact's ID: %s" % contact_entry.id.text)

	webnotes.conn.set_value("Contact",self.name,"contct_id", contact_entry.id.text)


def update_contact(info):
	webnotes.errprint("in the on_communication")

	with open('client.pickle') as pickle_file:
		client = pickle.load(pickle_file)
		webnotes.errprint(type(client))

	url = urllib2.unquote(info['id'].replace('base','full'))
	webnotes.errprint(url)
	contact_entry = client.GetContact(url)
	contact_entry.name.full_name.text = info['name']
	contact_entry.name.given_name.text = info['name']
	contact_entry.name.family_name.text = info['name']
	#contact_entry.email.address=info['email']
	#contact_entry.phone_number.text=info['phone']
	try:
			updated_contact = client.Update(contact_entry)
			webnotes.errprint('Updated: %s' % updated_contact.updated.text)

	except gdata.client.RequestError, e:
		if e.status == 412:
					pass



@webnotes.whitelist()
def get_google_authorize_url(client_id=None, client_secret=None, scope=None, user_agent=None, application_redirect_uri=None):
	request_token = generate_request_tocken(client_id, client_secret, scope, user_agent, application_redirect_uri)
	auth_url = request_token.generate_authorization_url()
	return str(auth_url)

def generate_request_tocken(client_id=None, client_secret=None, scope=None, user_agent=None, application_redirect_uri=None):
	if(client_id and client_secret and scope and user_agent and application_redirect_uri):
		"""Get request token."""
		client = gdata.contacts.client.ContactsClient(source=user_agent)
		request_token = client.get_oauth_token(client.auth_scopes, application_redirect_uri, client_id, str(client_secret))
		with open('data.pickle', 'w') as pickle_file:
			pickle.dump(request_token, pickle_file)
		return request_token
	
	else:
		webnotes.msgprint(" Please specify values for CLIENT ID, CLIENT_SECRET, SCOPE, USER_AGENT and APPLICATION_REDIRECT_URI ",raise_exception=1)

@webnotes.whitelist()
def g_callback(verification_code=None, user_agent=None):
	with open('data.pickle') as pickle_file:
		rqst_token = pickle.load(pickle_file)

	if verification_code and user_agent:
		client = gdata.contacts.client.ContactsClient(source=user_agent)
		gdata.gauth.authorize_request_token(rqst_token, verification_code)
		"""Get all contacts."""
		client.auth_token = client.get_access_token(rqst_token)
	
		with open('client.pickle', 'w') as pickle_file:
			pickle.dump(client, pickle_file)
		webnotes.msgprint("Updated")

@webnotes.whitelist()
def read_contact():
	with open('client.pickle') as pickle_file:
		client = pickle.load(pickle_file)

	query = gdata.contacts.client.ContactsQuery(max_results=25, showdeleted='True', updated_min=None, updated_max=None)

	# to rerieve contacts from google
	feed = client.get_contacts(query=query)
	for contact in feed.entry:
		try:
			webnotes.errprint(contact.id)
			webnotes.errprint(contact.name)
		except err:
			webnotes.errprint(err.message)


