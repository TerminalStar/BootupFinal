/**
 * Given an alert element, message and type of message, show the alert to the user.
 * The colour and iconography used depends on the given type of the alert.
 * Alert in this sense refers to Bootstrap alerts.
 *
 * @param Obj    feedback_alert Alert element on page to show
 * @param String message        Alert message to display to user
 * @param String type           Type of alert being conveyed, e.g 'error'
 *
 * @return Bool True if message has been displayed, false if the type param isn't recognised.
 */
function display_alert(feedback_alert, message, type)
{
    var alert_class = '';

    switch (type)
    {
        case 'error':
            alert_class    = 'alert-danger';
            glyphicon_type = 'remove';
            break;
        case 'warning':
            alert_class    = 'alert-warning';
            glyphicon_type = 'info';
            break;
        case 'success':
            alert_class    = 'alert-success';
            glyphicon_type = 'ok';
            break;
        default:
            return false;
            break;
    }

    var feedback_text = feedback_alert.find('p');

    feedback_alert.addClass(alert_class);
    feedback_text.append('<span class="glyphicon glyphicon-' + glyphicon_type + '"></span> ' + message);

    feedback_alert.slideDown(500).delay(2000).slideUp(500, function()
    {
        feedback_text.empty();
        feedback_alert.removeClass(alert_class);
    });
    
    return true;
}

/**
 * Validate input security code for a card.
 * Should be in a three digit long number.
 *
 * @param Int|String security_code Made of 3 digits.
 *
 * @return Bool True if security_code validates, false otherwise.
 */
function validate_security_code(security_code)
{
    var code_regex = /^\d{3}$/g;

    if (code_regex.test(security_code))
    {
        return true;
    }

    return false;
}

/**
 * Validate card number.
 * Should be 12 digits long.
 *
 * @param Int|String card_number Made of 12 digits.
 *
 * @return Bool True if card_number validates, false otherwise.
 */
function validate_card_number(card_number)
{
    var number_regex = /^\d{12}$/g;

    if (number_regex.test(card_number))
    {
        return true;
    }

    return false;
}

/**
 * Validate user password.
 * Should have a minimum length of 6.
 *
 * @param String password
 *
 * @return Bool True if password validates, false if not.
 */
function validate_password(password)
{
    var password_regex = /^.{6}.*$/g

    if (password_regex.test(password))
    {
        return true;
    }

    return false;
}

/**
 * Validate address post code.
 * Should be of the form XXXX XXX, where the first two are characters, the next 3 are numbers and the last two are characters.
 *
 * @param String post_code
 *
 * @return Bool True if post_code validates, false otherwise.
 */
function validate_post_code(post_code)
{
    var post_code_regex = /^([A-Za-z]){2}(\d){2}([ ])?(\d){1}([A-Za-z]){2}$/g

    if (post_code_regex.test(post_code))
    {
        return true;
    }

    return false;
}

/**
 * Format a given year, month and day combination into a database date-compatible format,
 * i.e. YYYY-MM-DD
 *
 * @param Int year  Either 2 or 4 digits long. If 2 digits, the full year is assumed to be 19XX
 * @param Int month
 * @param Int day
 *
 * @return String Formatted YYYY-MM-DD or empty if any parameter is empty once stripped of whitespace.
 */
function format_date(year, month, day)
{
    var year  = year.replace(/ /g, ''),
        month = month.replace(/ /g, ''),
        day   = day.replace(/ /g, '');

    if (year == '' || month == '' || day == '')
    {
        return ''
    }

    var year_regex = /^\d{2}$/,
        fulldate   = new Date(year, month - 1, day);

    if (year_regex.test(year))
    {
        // 2 digit year, to compare we want 4
        year = '19' + year.toString();
    }

    if (fulldate.getFullYear() == year && fulldate.getMonth() + 1 == month && fulldate.getDate() == day)
    {
        // Date validated
        return fulldate.getFullYear().toString() + '-' + (fulldate.getMonth() + 1).toString() + '-' + fulldate.getDate().toString();
    }
     
    return '';
}

/**
 * Format card expiry into full date (based on year and month).
 * Uses fact that Date(year, month, 0) gets the last day of the month previous.
 *
 * @param Int year  Assumed 2 digit.
 * @param Int month
 *
 * @return String YYYY-MM-DD format, last day of month
 */
function format_card_expiry(year, month)
{
    var year  = year.replace(/ /g, ''),
        month = month.replace(/ /g, '');

    if (year == '' || month == '')
    {
        return '';
    }

    var full_year = '20' + year,
        now       = new Date(),
        expiry    = new Date(full_year, month, 0);

    if (expiry.getTime() < now.getTime())
    {
        // Date in past
        return '';
    }
    
    return expiry.getFullYear().toString() + '-' + (expiry.getMonth() + 1).toString() + '-' + expiry.getDate().toString();
}
