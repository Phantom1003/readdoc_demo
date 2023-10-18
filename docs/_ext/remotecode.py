from docutils import nodes
from docutils.parsers.rst import directives

from sphinx.locale import _, __
from sphinx.directives.code import LiteralInclude
from sphinx.errors import SphinxError

from utils import check_file_exist

import json

class RemoteCodeError(SphinxError):
    category = 'RemoteCode error'

class RemoteCodeDirective(LiteralInclude):
    has_content = True
    option_spec = LiteralInclude.option_spec.copy()
    option_spec['url'] = directives.path
    option_spec['type'] = directives.path

    def run(self):
        local_path = self.arguments[0]
        url = self.options.pop('url', None)
        check_file_exist(local_path, url)

        file_type = self.options.pop('type', 'raw')
        if file_type == 'github-permalink':
            with open(local_path, "r") as json_file:
                data = json.load(json_file)
                if "payload" in data and "blob" in data["payload"] and "rawLines" in data["payload"]["blob"]:
                    raw = data["payload"]["blob"]["rawLines"]
                else:
                    raise RemoteCodeError(
                        __(f'Invalid Github permalink {url}')
                    )

                with open(f"{local_path}.done", "w") as output_file:
                    output_file.write('\n'.join(raw))

            self.arguments[0] = f"{local_path}.done"

            anno = url.split('/')[-1]
            highlight_lines = []
            if '#' in anno:
                highlight = anno.split('#')[-1].replace('L', '').split('-')
                try:
                    if len(highlight) == 1:
                        highlight_lines.append(int(highlight[0]))
                    else:
                        start = int(highlight[0])
                        end = int(highlight[1]) + 1
                        if start > end:
                            raise ValueError
                        highlight_lines.extend(range(start, end))
                except ValueError:
                        raise RemoteCodeError(
                            __(f'Invalid Github permalink {url}')
                        )
                
                if 'lines' in self.options and 'lineno-match' in self.options:
                    lines = self.options['lines']
                    starts = []
                    for group in lines.split(','):
                        starts.append(int(group.split('-')[0]))
                    
                    highlight_lines = [x - min(starts) + 1 for x in highlight_lines]
                
                self.options['emphasize-lines'] = ','.join([str(x) for x in highlight_lines])
                # print(self.options['lines'], self.options['lineno-match'], highlight_lines, self.options['emphasize-lines'])

        return super().run()

def setup(app):
    app.add_directive('remotecode', RemoteCodeDirective)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
