# Import modules used by more than 1 function
from gluon.custom_import import track_changes
track_changes(True)
import custom_functions
import json

# Get project categories and count of open Bootables within each
# Return dictionary containing category information and Bootable count
def discover():
    category_count = db.projects.category_id.count()
    categories     = db().select(db.project_categories.ALL)
    
    for category in categories:
        # Only get projects that are open for pledges
        project_count = db((db.projects.category_id == db.project_categories.id) & 
                            (db.project_categories.id == category.id) & 
                            (db.project_status.id == db.projects.status_id) & 
                            (db.project_status.name == 'open')
                          ).select(category_count).first().as_dict()

        category['project_count'] = project_count['_extra']['COUNT(projects.category_id)']

    return dict(
        categories = categories
    )

# Get all data for requested Bootable
# Return dictionary containg:
#   - project information
#   - pledges
#   - users who have pledged
#   - rewards for the pledgers
#   - current funding value
#   - funding goal formatted for display
#   - percent of funding achieved
#   - whether the current logged in user has pledged
#   - details of the pledge made by current user
#   - all rewards for the user
#   - whether the rewards stack or not
def view():
    if not(request.vars.has_key('project_id')):
        redirect(URL('default', 'index.html'))

    project = db((db.projects.id == request.vars.project_id) & 
                    (db.projects.category_id == db.project_categories.id) & 
                    (db.projects.status_id == db.project_status.id)
                ).select().first()

    if project.project_status.name != 'open':
        # Only Bootables open for pledges are to allowed to be viewed
        redirect(URL('errors', 'generic.html', vars=dict(error_details='project_unavailable')))

    # Calculate currently funded amount
    current_funding   = get_project_funding(request.vars.project_id);
    current_formatted = custom_functions.format_pounds(current_funding);

    # Get funding goal and calculate the percent funded so far
    required_funding = db(db.projects.id == request.vars.project_id).select(db.projects.funding_goal).first().as_dict()
    funding_goal     = required_funding['funding_goal']
    funding_percent  = int((float(current_funding)/float(funding_goal)) * 100)

    # Get project pledges and users who have purchased them
    pledges  = db(db.pledges.project_id == request.vars.project_id).select()
    pledgers = db((db.users_pledged.user_id == db.auth_user.id) & 
                    (db.pledges.id == db.users_pledged.pledge_id) & 
                    (db.pledges.project_id == request.vars.project_id)
                  ).select(
                        db.auth_user.first_name, 
                        db.auth_user.email, 
                        db.auth_user.id, 
                        db.pledges.value, 
                        db.pledges.id)

    # Find out if this project has stackable pledges
    # If so, get all rewards up to and including each pledger's pledge value
    # If not, just get the pledge purchased
    stack_status = db((db.projects.id == request.vars.project_id)).select(db.projects.include_lower_pledges).first().as_dict()
    pledger_rewards = {}

    if stack_status['include_lower_pledges']:
        for pledger in pledgers:
            project_id = get_project_id(pledger.pledges.id)
            rewards    = db((db.pledges.project_id == project_id) & 
                            (db.pledges.value <= pledger.pledges.value)
                           ).select()

            pledger_rewards[pledger.auth_user.id] = rewards
    else:
        for pledger in pledgers:
            rewards = db((db.pledges.id == pledger.pledges.id) & 
                         (db.pledges.value == pledger.pledges.value)).select()

            pledger_rewards[pledger.auth_user.id] = rewards

    # Format pledge values for display in for each pledger and each plege associated with this Bootable
    for pledger in pledgers:
        pledger.pledges.value = custom_functions.format_pounds(pledger.pledges.value)

    for pledge in pledges:
        pledge.value = custom_functions.format_pounds(pledge.value)

    has_pledged  = user_has_pledged(request.vars.project_id)
    pledge_made  = dict()
    user_rewards = dict()
 
    # Work out user's rewards if they have pledged to the project
    if has_pledged:
        pledge_made = db((db.users_pledged.user_id == auth.user.id) & 
                         (db.pledges.project_id == request.vars.project_id) & 
                         (db.pledges.id == db.users_pledged.pledge_id)
                        ).select(
                            db.pledges.value, 
                            db.users_pledged.pledge_id).first().as_dict()

        # Stacked means user gets rewards up to and including chosen pledge
        # Otherwise, just get the reward from the one chosen
        if stack_status['include_lower_pledges']:
            user_rewards = db((db.pledges.id == pledge_made['users_pledged']['pledge_id']) &
                                (db.pledges.value <= pledge_made['pledges']['value'])
                             ).select()
        else:
            user_rewards = db((db.pledges.id == pledge_made['users_pledged']['pledge_id'])).select()

        pledge_made['pledges']['value'] = custom_functions.format_pounds(pledge_made['pledges']['value'])

    formatted_goal = custom_functions.format_pounds(project['projects']['funding_goal'])

    return dict(
        project         = project,
        pledges         = pledges,
        pledgers        = pledgers,
        pledger_rewards = pledger_rewards,
        actual_funding  = current_formatted,
        formatted_goal  = formatted_goal,
        funding_percent = funding_percent,
        has_pledged     = has_pledged,
        pledge_made     = pledge_made,
        user_rewards    = user_rewards,
        rewards_stack   = stack_status['include_lower_pledges']
    )

# Search either category or title/short description of all open for pledges Bootables
# Return dictionary with title for page (category vs. search query) and results
def search():
    if request.vars.has_key('project_search'):
        query_results = db(((db.projects.title.contains(request.vars.project_search)) | 
                                (db.projects.short_description.contains(request.vars.project_search))) & 
                                (db.project_categories.id == db.projects.category_id) & 
                                (db.projects.status_id == db.project_status.id) & 
                                (db.project_status.name == 'open')
                          ).select()
    elif request.vars.has_key('category'):
        query_results = db((db.projects.category_id == db.project_categories.id) & 
                            (db.project_categories.description == request.vars.category) & 
                            (db.projects.status_id == db.project_status.id) & 
                            (db.project_status.name == 'open')).select()
    
    if request.vars.has_key('category'):
        title = request.vars.category
    else:
        title = 'Results for \'' + request.vars.project_search + '\''

    return dict(
        title   = title,
        results = query_results
    )

# Allow logged in users view creation screen
# Return dictionary with category details
@auth.requires_login()
def create():
    categories = db().select(db.project_categories.ALL)

    return dict(
        categories = categories
    )

# Allow logged in users to actually create the Bootable
# Return either string 'False' if creation fails or editor_url to redirect to
@auth.requires_login()
def create_new():
    title       = request.vars.title
    category_id = request.vars.category
    owner_id    = auth.user.id

    project = db.projects.insert(title = title, category_id = category_id, owner_id = owner_id)

    if (project == 'None'):
        return 'False'
    else:
        editor_url = URL('projects', 'editor.html', vars=dict(project_id=project))
        return editor_url

# Allow logged in users to edit a Bootable - but only if they are the manager
# Return dictionary with editable status of Bootable, Bootable details, category details and Bootable's pledges
@auth.requires_login()
def editor():
    project_id     = request.vars.project_id
    project        = db(db.projects.id == project_id).select().first()
    project_status = db(db.project_status.id == project.status_id).select(db.project_status.name).first().as_dict()
    project.status = project_status['name']

    if (auth.user.id != project.owner_id):
        # Redirect to error if current user isn't the Bootable Manager
        redirect(URL('errors', 'generic.html', vars=dict(error_details = 'no_permission')))
    elif project.status == 'open':
        # Prevent editing an open Bootable
        return dict(
            editable = False
        )
    else:
        categories = db().select(db.project_categories.ALL)
        pledges    = db(db.pledges.project_id == project_id).select(orderby=db.pledges.value)

        for pledge in pledges:
            # Convert each pledge value into pounds
            pledge.value = custom_functions.format_pounds(pledge.value)

        return dict(
            editable   = True,
            project    = project,
            categories = categories,
            pledges    = pledges
        )

# Allow logged in managers to update their Bootables
# Return ID of the updated project (or None, if the update fails)
@auth.requires_login()
def update_project():
    if not is_project_owner(auth.user.id, request.vars.project_id):
        # Don't allow update if user isn't the Bootable Manager
        redirect(URL('errors', 'generic.html', vars=dict(error_details = 'no_permission')))

    project_id    = request.vars.project_id
    update_values = dict()
    del request.vars.project_id

    if 'funding_goal' in request.vars:
        # Needs to be input as integer, in pence to db
        # Replace commas if they've been input
        request.vars.funding_goal    = request.vars.funding_goal.replace(',', '')
        request.vars['funding_goal'] = custom_functions.calculate_pence(request.vars.funding_goal)

    for value in request.vars:
        update_values[value] = request.vars[value]

    updated = db(db.projects.id == project_id).update(**update_values)

    return updated

# Add new pledge
# Return new pledge ID (or None if insert fails)
@auth.requires_login()
def add_pledge():
    pledge_details = dict()

    if 'value' in request.vars:
        # Convert input pounds to pence for db entry
        request.vars['value'] = custom_functions.calculate_pence(request.vars.value.replace(',', ''))

    for value in request.vars:
        pledge_details[value] = request.vars[value]

    inserted = db.pledges.insert(**pledge_details)

    return inserted

# Edit an existing pledge
# Return pledge ID of updated pledge (or None if update fails)
@auth.requires_login()
def update_pledge():
    pledge_id      = request.vars.pledge_id
    pledge_details = dict()
    del request.vars.pledge_id

    if 'value' in request.vars:
        # Needs input as integer pence
        request.vars['value'] = custom_functions.calculate_pence(request.vars.value)

    for value in request.vars:
        pledge_details[value] = request.vars[value]

    updated = db(db.pledges.id == pledge_id).update(**pledge_details)

    return updated

# Delete a pledge
# Returns number of table rows affected by delete
@auth.requires_login()
def delete_pledge():
    if not request.vars.pledge_id:
        return 'None';

    deleted = db(db.pledges.id == request.vars.pledge_id).delete()

    return deleted

# Move Bootable from open for pledges to either funded (if met goal) or not funded (hasn't met goal)
# Return JSON encoded dictionary of:
#   - result; True if an updated occured, False otherwise
#   - new_status; Funded if enough money has been pledged, not funded otherwise
@auth.requires_login()
def close_project():
    if not request.vars.project_id or not is_project_owner(auth.user.id, request.vars.project_id):
        # Don't allow a user who isn't the Bootable Manager to close a project
        return json.dumps(
            dict(
                result = False
            )
        )

    project_goal  = db(db.projects.id == request.vars.project_id).select(db.projects.funding_goal).first().as_dict()
    total_funding = get_project_funding(request.vars.project_id)

    if total_funding < project_goal['funding_goal']:
        status = 'not_funded'
    else:
        status = 'funded'

    new_status = db(db.project_status.name == status).select(db.project_status.id, db.project_status.description).first().as_dict()

    updated = db(db.projects.id == request.vars.project_id).update(status_id = new_status['id'])

    return json.dumps(
        dict(
            result = type(updated) is int,
            new_status = new_status['description']
        )
    )

# Move Bootable from not available/not funded to open for pledges
# Return JSON encoded dictionary of:
#   - result; True if an update has occurred, False otherwise
#   - new_status; Open for Pledges
@auth.requires_login()
def open_project():
    if not request.vars.project_id or not is_project_owner(auth.user.id, request.vars.project_id):
        return 'None';

    new_status = db(db.project_status.name == 'open').select(db.project_status.id, db.project_status.description).first().as_dict()

    updated = db(db.projects.id == request.vars.project_id).update(status_id = new_status['id'])

    return json.dumps(
        dict(
            result     = type(updated) is int,
            new_status = new_status['description']
        )
    )

# Open Bootable for the first time (from editor page).
# Redirect to view page because you're not allowed to edit after opening
@auth.requires_login()
def publish_project():
    project_id    = request.vars.project_id
    update_status = db(db.project_status.name == 'open').select().first()
    updated = db(db.projects.id == project_id).update(**dict(status_id = update_status.id))

    redirect(URL('projects', 'view.html', vars=dict(project_id = project_id)))

# Submit a user's purchase of a pledge
# Return JSON encoded dictionary
#   - highest_pledge; value of the pledge selected, formatted to pounds
#   - all_pledges; if project has stackable pledges, this includes all pledges below highest_pledge value, otherwise just the selected pledge
@auth.requires_login()
def submit_pledge():
    if not request.vars.pledge_id:
        return dict()

    added        = db.users_pledged.insert(pledge_id = request.vars.pledge_id, user_id = auth.user.id)
    stack_status = db((db.projects.id == db.pledges.project_id) & 
                        (db.pledges.id == request.vars.pledge_id)
                     ).select(db.projects.include_lower_pledges).first()

    value_submitted = db(db.pledges.id == request.vars.pledge_id).select(db.pledges.value).first().as_dict()

    if stack_status.include_lower_pledges:
        project_id  = get_project_id(request.vars.pledge_id)
        all_pledges = db((db.pledges.id == request.vars.pledge_id) & (db.pledges.value <= value_submitted['value'])).select().as_dict()
    else:
        all_pledges = db(db.pledges.id == request.vars.pledge_id).select().as_dict()

    highest_pledge = custom_functions.format_pounds(value_submitted['value'])

    return json.dumps(
        dict(
            highest_pledge = highest_pledge,
            all_pledges    = all_pledges
        )
    )

# Save Bootable image to file system
# Return True once image has been uploaded
def upload_image():
    if 'image' in request.vars:
        import shutil
        import os
        
        # Strip any leading paths to avoid directory traversal attacks
        filename   = os.path.basename(request.vars.image.filename)

        # Strip whitespace
        clean_filename = ''.join(filename.split())
        image_file     = request.vars.image.file

        image_directory = 'applications' + URL('static', 'images') + '/' + clean_filename

        # Save to file system
        shutil.copyfileobj(image_file,open(image_directory,'wb'))

        return True

# Get total amount funded for a given Bootable ID
# Return total funded amount, or 0 if a Bootable ID isn't passed in
def get_project_funding(project_id):
    if not project_id:
        return 0

    total_funding = 0
    pledge_count  = db.users_pledged.user_id.count()

    # Get pledge details and count of how many users have purchased that pledge
    funding = db((db.pledges.project_id == project_id) & 
                        (db.users_pledged.pledge_id == db.pledges.id)
                      ).select(
                            db.pledges.value, 
                            db.users_pledged.pledge_id, 
                            pledge_count, 
                            groupby=db.pledges.id)

    for pledge in funding:
        pledge_total   = pledge.pledges.value * pledge._extra['COUNT(users_pledged.user_id)']
        total_funding += pledge_total

    return total_funding

# Work out if the currently logged in user has pledged to the given Bootable ID
# Return True if they have, False if they're not logged in or they haven't pledged
def user_has_pledged(project_id):
    if not project_id or not auth.is_logged_in():
        return False

    already_pledged = db((db.users_pledged.user_id == auth.user.id) & (db.pledges.id == db.users_pledged.pledge_id) & (db.pledges.project_id == project_id)).select(db.users_pledged.id.count()).first().as_dict()

    if already_pledged['_extra']['COUNT(users_pledged.id)'] > 0:
        return True
    else:
        return False

# See if given user ID is the owner of the given Bootable ID
# Return True if they are, False if not
def is_project_owner(user_id, project_id):
    if not user_id or not project_id:
        return false

    is_project_owner = db((db.projects.id == project_id) & (db.projects.owner_id == user_id)).count() 
    
    return is_project_owner

# Get Bootable ID from pledge ID
# Return Bootable ID
def get_project_id(pledge_id):
    project_id = db(db.pledges.id == pledge_id).select(db.pledges.project_id).first().as_dict()

    return project_id['project_id']
