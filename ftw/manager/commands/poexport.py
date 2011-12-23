from ftw.manager.commands import basecommand
import os
from ftw.manager.utils import output, runcmd
from i18ndude import catalog
from xlwt import Workbook

class ExportPo(basecommand.BaseCommand):
    u"""Expots Po files to a XLS"""
    
    command_name = u'poexport'
    command_shortcut = u'pe'
    description = u'exports all po files to xls'
    usage = u'ftw %s [LANG-CODE] [OPTIONS]' % command_name
    
    def __call__(self):
    
        if len(self.args) < 1:
            output.error('Language code is required', exit=1)
        lang = self.args[0]
        workingpath = os.getcwd()
        if os.path.basename(workingpath) != "src":
            output.error("The working Path is not a source directory", exit=1)
            return
        if self.options.original:
            origlang = self.options.original
        
        potfiles = self.get_potfiles(workingpath)
        translations = []
        for potfile in potfiles:
            locales = os.path.dirname(potfile)
            if origlang:
                origlangdir = locales +'/'+origlang+'/LC_MESSAGES/'
                os.system("mkdir -p %s" % origlangdir)
                old_po = origlangdir +os.path.splitext(os.path.basename(potfile))[0]+'.po'
                os.system("i18ndude sync --pot %s %s > /dev/null" % (potfile, old_po))
            langdir = locales +'/'+lang+'/LC_MESSAGES/'
            os.system("mkdir -p %s" % langdir)
            new_po = langdir + os.path.splitext(os.path.basename(potfile))[0]+'.po'
            if not os.path.isfile(new_po):
                os.system("touch %s" % new_po)
            # Advised by jones
            os.system("i18ndude sync --pot %s %s > /dev/null" % (potfile, new_po))
            messages = catalog.MessageCatalog(old_po)
            new_messages = catalog.MessageCatalog(new_po)
            for message in new_messages.values():
                default = message.getDefault()
                if default:
                    default = default.decode('utf-8')
                if len([line for line in message.comments if 'fuzzy' in line.lower()]) > 0:
                    print "\n*******\nWARNING\n*******"
                    print "Message_ID '" + message.msgid + "' is fuzzy in file " + new_po +"\n\n" 
                if messages.has_key(message.msgid):
                    translations.append([{message.msgid:message.msgstr}, default,
                        new_po, messages.get(message.msgid).msgstr ])
                else:
                    translations.append([{message.msgid:message.msgstr}, default, new_po])
        wb = Workbook()
        sheet = wb.add_sheet("Translations")
        sheet.write(0,4, "Path")
        sheet.write(0,0, "Message_ID")
        sheet.write(0,1, "Default")
        sheet.write(0,2, origlang+" Translation")
        sheet.write(0,3, lang+" Translation (Translated)")
        
        print str(len(translations)) + " Message_IDs found."
        untranslated = 0
        for i, translation in enumerate(translations):
            key, value = translation[0].items()[0]
            if not value:
                untranslated += 1
            path = translation[2]
            sheet.write(i+1,4, path)
            sheet.write(i+1,0, key)
            sheet.write(i+1,1, translation[1])
            sheet.write(i+1,3, value)
            if len(translation) == 4:
                sheet.write(i+1,2, translation[3])
                
        print str(untranslated) + " Message_IDs have no Translations."
        wb.save('translations.xls')

    def get_potfiles(self, path):
        potfiles = runcmd('find . -name "*.pot"', respond=True)
        clean_pofiles = []
        for potfile in potfiles:
            if '/i18n/' in potfile:
                continue
            if '-manual' in potfile:
                continue
            else:
                clean_pofiles.append(potfile.strip()) 
        return clean_pofiles

    def register_options(self):
        self.parser.add_option('-o', '--original', dest='original',
                               action='store', default=None,
                               help='Original Domain. Default: nothing')


basecommand.registerCommand(ExportPo)