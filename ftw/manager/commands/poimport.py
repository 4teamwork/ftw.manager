from ftw.manager.commands import basecommand
import os
from ftw.manager.utils import output
from i18ndude import catalog
import xlrd
from types import NoneType
from ftw.manager.utils import runcmd_with_exitcode


class ImportPo(basecommand.BaseCommand):
    u"""Imports translation from xls"""
    command_name = u'poimport'
    command_shortcut = u'pi'
    description = u'imports an xls file with translations for specific po files'
    usage = u'ftw %s [OPTIONS]' % command_name
    
    
    def __call__(self):
        self.message_storages = {}
        file_ = self.args[0]
        wb = xlrd.open_workbook(file_)
        self.sheet = wb.sheets()[0]
        for counter, cell in enumerate(self.sheet.row(0)):
            if '(Translated)' in cell.value:
                self.translated_column = counter
        if not self.translated_column:
            output.error("No Translated Column was found", exit=1)
            return
        for i in range(1, self.sheet.nrows):
            values = self.sheet.row_values(i)
            path = values[-1]
            msgid = values[0]
            msgstr = values[self.translated_column]
            self.write_in_catalog(path,msgid,msgstr)
        self.write_all_catalogs()
    
    
    def write_in_catalog(self, path, msgid, msgstr):
        if not os.path.isfile(path):
            return
        if not self.message_storages.has_key(path):
            self.sync_po(path)
            self.message_storages[path] = catalog.MessageCatalog(path)
        cat = self.message_storages[path]
        message = cat.get(msgid)
        if isinstance(message, NoneType):
            return
        message.msgstr = msgstr

        
    def sync_po(self, path):
        domain = os.path.splitext(os.path.basename(path))[0]
        locales = path.split('/')[:-3]
        pot = '/'.join(locales)+'/'+domain+'.pot'
        os.system('i18ndude sync --pot %s %s > /dev/null' % (pot, path))        
        return


    def write_all_catalogs(self):
        for key in self.message_storages.keys():
            value = self.message_storages.get(key)
            file_ = open(key, 'w')
            writer = catalog.POWriter(file_, value)
            writer.write(msgstrToComment=False, sync=True)
            file_.close()
            data = open(key).read().split('\n')
            file_ = open(key, 'w')
            for row in data:
                if not row.startswith('"Language-Code') and \
                        not row.startswith('"Language-Name'):
                    file_.write(row)
                    if not data.index(row)  == len(data)-1:  
                        file_.write('\n')
            file_.close()

            print "Wrote PO-File %s" % key
            #check pofile with msgfmt
            exitcode, errors = runcmd_with_exitcode(
                'msgfmt -o /dev/null %s' % key,
                log=False,
                respond_error=True)
            if exitcode > 0:
                output.error(errors, exit=False)




basecommand.registerCommand(ImportPo)