# Return a page with a generic error alert on it
# Mostly for redirects when trying to directly access Bootable views, editor etc.
def generic():
    if request.vars.error_details == 'project_unavailable':
        error_message = 'I\'m sorry, the project you were trying to view is currently unavailable.'
    elif request.vars.error_details == 'no_permission':
        error_message = 'I can\t let you do that. Sorry, you don\'t have permission!'

    return dict(
        error_message = error_message
    )
