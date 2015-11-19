db = DAL('sqlite://storage.db')

from gluon.tools import Auth
auth = Auth(db)
auth.settings.extra_fields['auth_user']= [
        Field('birthdate', 'date')]
auth.define_tables(username=False,signature=False)
auth.settings.controller = 'user'
auth.settings.login_url = URL('user', 'login')
auth.settings.on_failed_authentication = URL('user', 'login')
auth.settings.password_min_length = 6
auth.settings.login_after_registration = True

#id field addresses.id
db.define_table('addresses',
        Field('street_address', 'string', required=True), 
        Field('city', 'string', required=True),
        Field('country', 'string', required=True),
        Field('post_code', 'string', length = 7, required=True),
        Field('billing_address', 'boolean', default=False),
        Field('user_id', auth.settings.table_user, required=True)
)

#id field is credit_cards.id
db.define_table('credit_cards',
        Field('number', 'string', length = 12, required=True),
        Field('expiry_date', 'date', required=True),
        Field('security_code', 'string', length = 3, required=True),
        Field('billing_address_id', db.addresses, required=True),
        Field('user_id', auth.settings.table_user, required=True)
)

db.define_table('project_categories',
        Field('description', 'string', required=True, unique=True)
)

db.define_table('project_status',
        Field('description', 'string', required=True, unique=True),
        Field('name', 'string', required=True, length=10, unique=True)
)

db.define_table('projects',
        Field('title', 'string', required=True),
        Field('short_description', 'string', length=120), #small limit
        Field('long_description', 'string'), #needs to be much longer than short one
        Field('funding_reason', 'text'),
        Field('category_id', db.project_categories, required=True), #references categories.id
        Field('funding_goal', 'integer', default=0), #store in pence, avoid rounding error(s)
        Field('image', 'upload'),
        Field('include_lower_pledges', 'boolean', default=False),
        Field('creation_date', 'datetime', default=request.now),
        Field('status_id', db.project_status, default=1), #references project_status.id, defaults to Not Available
        Field('owner_id', auth.settings.table_user, required=True) #references users.id of owner
)

db.define_table('pledges',
        Field('project_id', db.projects, required=True), #projects.id
        Field('value', 'integer', required=True),
        Field('description', 'string', required=True)
)

db.define_table('users_pledged',
    Field('pledge_id', db.pledges, required=True),
    Field('user_id', auth.settings.table_user, required=True)
)
