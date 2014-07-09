// Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

wn.require('app/controllers/js/contact_address_common.js');

cur_frm.cscript.refresh = function(doc) {
	cur_frm.communication_view = new wn.views.CommunicationList({
		list: wn.model.get("Communication", {"parent": doc.name, "parenttype": "Contact"}),
		parent: cur_frm.fields_dict.communication_html.wrapper,
		doc: doc,
		recipients: doc.email_id
	});
}

cur_frm.cscript.hide_dialog = function() {
	if(cur_frm.contact_list)
		cur_frm.contact_list.run();
}


cur_frm.cscript.allow_google_contact_access = function(doc, dt, dn) {
	console.log([doc.client_id, doc.client_secret, doc.scope, doc.user_agent, doc.application_redirect_uri])
	return wn.call({
		method: "selling.doctype.google_contact.google_contact.get_google_authorize_url",
		args: {
			client_id: doc.client_id,
			client_secret: doc.client_secret,
			scope:doc.scope,
			user_agent: doc.user_agent,
			application_redirect_uri: doc.application_redirect_uri
		},
		callback: function(r) {
			console.log(r)
			if(!r.exc) {
				window.open(r.message);
			}
		}
	});
}

cur_frm.cscript.generate_auth_tocken = function(doc, dt, dn) {
	console.log(doc.request_token)
	return wn.call({
		method: "selling.doctype.google_contact.google_contact.g_callback",
		args: {
			verification_code: doc.request_token,
			user_agent: doc.user_agent
		},
	});
}

cur_frm.cscript.read_contact = function(doc, dt, dn) {
	// console.log(doc.request_token)
	wn.call({
		method: "selling.doctype.google_contact.google_contact.read_contact",
	});
}