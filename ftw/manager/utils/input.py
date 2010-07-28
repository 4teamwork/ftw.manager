
import output

def something_validator(value):
    return value and len(value)>0

def prompt(prompt, validator=None):
    """
    validator: validator function
        def validator(value):
            if value:
                return True
            else:
                return 'No Way'
    """
    def ask():
        return raw_input(output.colorize('  %s > ' % prompt, output.WARNING))
    if validator:
        def looper(input):
            val = validator(input)
            if val!=True:
                output.warning(str(val))
                return True
            else:
                return False
        input = ask()
        while looper(input):
            input = ask()
        return input
    else:
        return ask()


# Boolean

def prompt_bool(text, default=True):
    negative = ['no', 'nein', 'n', 'false', '0',]
    positive = ['yes', 'ja', 'j', 'y', 'true', '1', ]
    if default==True:
        positive.append('')
    elif default==False:
        negative.append('')
    def validator(value):
        return value.lower() in negative + positive and 1 or 'Yes or no?'
    text += default==True and ' [Y/n]' or default==False and ' [y/N]' or ' [y/n]'
    value = prompt(text, validator)
    return value in positive

