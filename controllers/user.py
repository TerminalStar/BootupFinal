# Import modules used by more than 1 function
from gluon.custom_import import track_changes
track_changes(True)
import custom_functions
import json
import datetime

# Signup page
# Returns dictionary of all months and all years (used in the sign up form)
def signup():
    return dict(
        all_months = custom_functions.get_months(),
        all_years  = custom_functions.get_years()
    )

# Login page
def login():
    return dict()

# Login user to be called via AJAX
# Returns new user details
def confirm_login():
    user = auth.login_bare(request.vars.username, request.vars.password)
    return user

# Register user, for use via AJAX
# Returns True if user's personal details and address and credit card are added, otherwise False
def confirm_signup():
    user_details = {
        'first_name': request.vars.first_name,
        'last_name': request.vars.last_name,
        'email': request.vars.email,
        'password': request.vars.password,
        'birthdate': request.vars.birthdate
    }

    user = auth.register_bare(**user_details)

    if user:
        address_details = {
            'street_address': request.vars.street_address,
            'city': request.vars.city,
            'country': request.vars.country,
            'post_code': request.vars.post_code,
            'billing_address': True,
            'user_id': user
        }

        address = db.addresses.insert(**address_details)

        if address:
            card_details = {
                'number': request.vars.number,
                'expiry_date': request.vars.expiry,
                'security_code': request.vars.security_code,
                'billing_address_id': address,
                'user_id': user
            }

            card = db.credit_cards.insert(**card_details)

            if card:
                return user

    return False

# Logout current user
def logout():
    auth.logout()
    return dict()

# Show user the Bootables they manage
# Return dictionary of Bootables
@auth.requires_login()
def projects():
    user_projects = db((db.projects.owner_id == auth.user.id) & (db.projects.status_id == db.project_status.id)).select()

    for project in user_projects:
        if project.project_status.name == 'open':
            project['formatted_goal']    = custom_functions.format_pounds(project.projects.funding_goal)
            project['formatted_funding'] = custom_functions.format_pounds(get_project_funding(project.projects.id))

    return dict(
        projects = user_projects
    )

# Show user their purchased pledges
# Returns dictionary of pledges the current user has made and any additional pledge rewards they get for Bootables with stacked pledges
# The additional pledges dictionary uses Bootable IDs as the keys, for easier reference in page
@auth.requires_login()
def pledges():
    user_pledges = db((db.users_pledged.user_id == auth.user.id) & 
                        (db.pledges.id == db.users_pledged.pledge_id) & 
                        (db.projects.id == db.pledges.project_id) &
                        (db.project_status.id == db.projects.status_id)
                     ).select()

    additional_pledges = dict()

    for (index, pledge) in enumerate(user_pledges):
        if pledge.projects.include_lower_pledges:
            funding = pledge.pledges.value

            # Add lower pledges when Bootable has stacked pledges
            additional_pledges[pledge.projects.id] = db((db.pledges.project_id == db.projects.id) & 
                                                            (db.projects.id == pledge.projects.id) & 
                                                            (db.pledges.value <= funding)
                                                       ).select(db.pledges.description)

        pledge.pledges.value         = custom_functions.format_pounds(pledge.pledges.value)
        pledge.projects.funding_goal = custom_functions.format_pounds(pledge.projects.funding_goal)
        pledge.projects.total_funded = custom_functions.format_pounds(get_project_funding(pledge.projects.id))

    return dict(
        pledges            = user_pledges,
        additional_pledges = additional_pledges
    )

# Show user their account page
# Return dictionary of:
#   - User addresses
#   - User credit cards
#   - User's billing addresses
#   - All months
#   - All years
#   - Calculated user age
@auth.requires_login()
def account():
    user_addresses    = dict(addresses = db(db.addresses.user_id == auth.user.id).select())
    user_cards        = dict(cards = db(db.credit_cards.user_id == auth.user.id).select())
    billing_addresses = db((db.addresses.billing_address == True) & (db.addresses.user_id == auth.user.id)).select(db.addresses.ALL)

    for card in user_cards['cards']:
        # Format expiry to show in-page as MM/YY
        card.formatted_expiry = datetime.datetime.strftime(card.expiry_date, '%m/%y')
    
    return dict(
        addresses         = user_addresses['addresses'],
        credit_cards      = user_cards['cards'],
        billing_addresses = billing_addresses,
        all_months        = custom_functions.get_months(),
        all_years         = custom_functions.get_years(),
        user_age          = calculate_age(auth.user.birthdate)
    )

# Update user table with submitted values
# Returns JSON encoded dictionary with result True if update is successful or False otherwise
@auth.requires_login()
def update_user():
    if not auth.user.id:
        redirect(URL('user', 'login'));

    update_values = dict()

    for value in request.vars:
        update_values[value] = request.vars[value]

    updated = db(db.auth_user.id == auth.user.id).update(**update_values)

    if type(updated) is int:
        if 'birthdate' in request.vars:
            # Birthdate needs converting to date object for entering to database
            birthdate = request.vars.birthdate.split('-')
            update_values['birthdate'] = datetime.date(int(birthdate[0]), int(birthdate[1]), int(birthdate[2]))
            
        auth.user.update(**update_values)

    return json.dumps(
        dict(
            result = type(updated) is int
        )
    )

# Add new address for user
# Returns ID of inserted row if successful, None otherwise
@auth.requires_login()
def add_address():
    address_details = {
        'street_address': request.vars.street_address,
        'city': request.vars.city,
        'country': request.vars.country,
        'post_code': request.vars.post_code,
        'billing_address': True,
        'user_id': auth.user.id
    }

    address = db.addresses.insert(**address_details)

    return address

# Add new credit card for user
# Retuns ID of inserted row if successful, or None otherwise
@auth.requires_login()
def add_card():
    card_details = {
        'number': request.vars.number,
        'expiry_date': request.vars.expiry_date,
        'security_code': request.vars.security_code,
        'billing_address_id': request.vars.address_id,
        'user_id': auth.user.id
    }

    card = db.credit_cards.insert(**card_details)

    return card

# Change billing address associated with a credit card
# Returns ID of updated row if successful, None otherwise
@auth.requires_login()
def update_billing_address():
    update_values = dict(
        billing_address_id = request.vars.address_id
    )

    card = db(db.credit_cards.id == request.vars.card_id).update(**update_values)

    return card

# Delete a Bootable, but only if the current user is the manager
# Redirects to generic error page if user is not the manager
# Returns JSON encoded dictionary with result True if Bootable deleted or False otherwise
@auth.requires_login()
def delete_project():
    if not is_project_owner(auth.user.id, request.vars.project_id):
        redirect(URL('errors', 'generic.html', vars=dict(error_details='no_permission')))

    deleted = db(db.projects.id == request.vars.project_id).delete()

    if deleted:
        return json.dumps(
            dict(
                result = True
            )
        )
    else:
        return json.dumps(
            dict(
                result = False
            )
        )

# Calculate how much funding the given Bootable ID has so far
# Return total funding pledged so far
def get_project_funding(project_id):
    if not project_id:
        return 0
 
    total_funding = 0
    pledge_count  = db.users_pledged.user_id.count()
    funding       = db((db.pledges.project_id == project_id) &
                        (db.users_pledged.pledge_id == db.pledges.id)
                      ).select(
                            db.pledges.value, 
                            db.users_pledged.pledge_id, 
                            pledge_count,
                            groupby=db.pledges.id)
 
    for pledge in funding:
        # For each pledge, multiply its value by how many people have purchased it
        pledge_total = pledge.pledges.value * pledge._extra['COUNT(users_pledged.user_id)']
        total_funding += pledge_total
 
    return total_funding

# Check if given user is the owner of the given Bootable ID
# Return True if they are, False if not
def is_project_owner(user_id, project_id):
    if not user_id or not project_id:
        return false

    is_project_owner = db((db.projects.id == project_id) & (db.projects.owner_id == user_id)).count()

    return is_project_owner

# Calculate a person's age based on the given birthday - must be parseable by date function
# Return age, in years 
def calculate_age(born):
    today = datetime.date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
