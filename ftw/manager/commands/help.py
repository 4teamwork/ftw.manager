
import basecommand

class HelpCommand(basecommand.BaseCommand):
    """
    The ftw.manager egg provides various commands for daily work.
    """

    command_name = 'help'
    description = 'show help text'
    usage = '%%prog %s command' % command_name

    def __call__(self):
        if len(self.args)==0 or self.args[0]=='help':
            self.parser.print_usage()
        else:
            command = self.maincommand.get_command(self.args[0])
            if command:
                command(self.maincommand).parser.print_usage()
            else:
                self.parser.print_usage()

basecommand.registerCommand(HelpCommand)
