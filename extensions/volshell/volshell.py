import os
import re
import pexpect
from web.common import Extension
from web.database import Database
v = {'volshell_id': None, 'volshell_object': None}

class VolShell(Extension):

    # Paths should be relative to the extensions folder
    extension_name = 'VolShell'
    extension_type = 'toolbar'
    extra_js = 'volshell/volshell.js'

    def strip_ansi_codes(self, s):
        return re.sub(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]', '', s)

    def run(self):
        global v
        db = Database()
        session_id = self.request.POST['session_id']
        shell_input = self.request.POST['shell_input']
        if shell_input == 'resetvolshellsession':
            v = {'volshell_id': None, 'volshell_object': None}

        session = db.get_session(session_id)
        vol_shell_cmd = 'vol.py --profile={0} -f {1} volshell'.format(session['session_profile'],
                                                                       session['session_path']
                                                                       )

        # Determine if ipython is installed as this will change the expect regex
        try:
            import IPython
            expect_regex = '.*In .*\[[0-9]{1,3}.*\]:'

        except ImportError:
            expect_regex = '.*>>>'

        # Start or restore a shell

        if v['volshell_id']:
            voll_shell = v['volshell_object']
        else:
            voll_shell = pexpect.spawn(vol_shell_cmd)
            voll_shell.expect(expect_regex)
            v['volshell_id'] = session_id

        # Now run the inputs

        voll_shell.sendline(shell_input)

        voll_shell.expect(expect_regex, timeout=60)

        v['volshell_object'] = voll_shell

        before_data = self.strip_ansi_codes(voll_shell.before)
        after_data = self.strip_ansi_codes(voll_shell.after)
        #print "Before Data: ", before_data
        #print "After Data: ", after_data

        # lets start by getting input and returning it

        self.render_type = 'html'
        self.render_data = '<pre>{0}</pre>'.format(str(after_data))
        self.render_javascript = open(os.path.join('extensions', self.extra_js), 'rb').read()
