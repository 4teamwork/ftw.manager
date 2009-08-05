
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
        return raw_input(output.ColorString('  %s > ' % prompt, output.YELLOW))
    if validator:
        def looper():
            val = validator(ask())
            if val!=True:
                output.warning(val)
                return True
            else:
                return False
        while looper():
            pass
    else:
        return ask()
