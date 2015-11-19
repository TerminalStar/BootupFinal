# Bootup home page
def index():
    most_recent = db((db.projects.status_id == db.project_status.id) & 
                        (db.project_status.name == 'open') & 
                        (db.projects.category_id == db.project_categories.id)
                    ).select(
                        db.projects.ALL, 
                        db.project_categories.description, 
                        limitby=(0,5), 
                        orderby=~db.projects.creation_date)
    
    pledge_sum = db.pledges.value.sum()

    # Bootables with the smallest amount of funding required to meet their goal
    nearest_goal = db((db.projects.id == db.pledges.project_id) & 
                        (db.pledges.id == db.users_pledged.pledge_id) & 
                        (db.project_status.id == db.projects.status_id) & 
                        (db.project_status.name == 'open') & 
                        (db.projects.category_id == db.project_categories.id)
                     ).select(
                            pledge_sum, 
                            db.projects.funding_goal - pledge_sum, 
                            db.projects.ALL, 
                            db.project_categories.description, 
                            limitby = (0,5), 
                            orderby = (db.projects.funding_goal - pledge_sum), 
                            groupby = db.projects.id)

    for project in most_recent:
        project_id  = project.projects.id

        if has_pledges(project_id):
            # If there are existing pledges, we need the value of all of them
            # Then, we can work out the % achieved so far
            project_value = db((db.pledges.project_id == project_id) & 
                                (db.projects.id == project_id) & 
                                (db.users_pledged.pledge_id == db.pledges.id)
                              ).select(
                                    pledge_sum, 
                                    groupby = db.projects.id
                              ).first().as_dict()

            project['percent_achieved'] = int(float(project_value['_extra']['SUM(pledges.value)']) / float(project.projects['funding_goal']) * 100)
        else:
            # If there are no pledges, default to 0% funding achieved
            project['percent_achieved'] = 0

    for project in nearest_goal: 
        project['percent_achieved'] = int(float(project._extra['SUM(pledges.value)']) / float(project.projects['funding_goal']) * 100)

    return dict(
        most_recent  = most_recent,
        nearest_goal = nearest_goal
    )

# Determine whether a given Bootable ID has pledges or not
# Param Int project_id Bootable ID
# Return true if it has pledges, false otherwise
def has_pledges(project_id):
    pledges = db((db.projects.id == project_id) & 
                    (db.pledges.project_id == db.projects.id) & 
                    (db.pledges.id == db.users_pledged.pledge_id)
                ).select(db.projects.id.count()).first().as_dict()

    return pledges['_extra']['COUNT(projects.id)'] > 0
