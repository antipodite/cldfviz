"""

"""
import re
import pathlib
import argparse
import urllib.parse

from clldutils.clilib import PathType
from pycldf.cli_util import get_dataset, add_dataset
from termcolor import colored

from cldfviz.text import *
from . import map

MD_IMG_PATTERN = re.compile(r'!\[(?P<label>[^]]*)]\((?P<url>[^)]+)\)')


def register(parser):
    add_dataset(parser)
    parser.add_argument('-l', '--list', help='list templates', default=False, action='store_true')
    parser.add_argument('--text-string', default=None)
    parser.add_argument('--text-file', type=PathType(type='file', must_exist=True), default=None)
    parser.add_argument('--templates', type=PathType(type='dir'), default=None)


def run(args):
    ds = get_dataset(args)

    if args.list:
        print(colored('Available templates:', attrs=['bold', 'underline']) + '\n')
        for p, doc, vars in iter_templates():
            component, _, type_ = p.stem.partition('_')
            if (component == 'Source' and ds.sources) or component in ds:
                print(colored('{} {}'.format(component, type_), attrs=['bold']))
                print('Usage: ' + colored('[<label>]({}{}#cldf:{})'.format(
                    component,
                    '?var1&var2' if vars else '',
                    '__all__' if type_ == 'index' else '<object-ID>'), color='blue'))
                if vars:
                    print('Variables: ' + colored(', '.join(vars), color='blue'))
                if doc:
                    print(doc)
        return

    assert args.text_string or args.text_file
    res = render(
        args.text_string or args.text_file.read_text(encoding='utf8'), ds, args.templates)
    create_maps(args, res, ds, pathlib.Path('.') if args.text_string else args.text_file.parent)
    print(res)


def create_maps(oargs, md, ds, base_dir):
    for m in MD_IMG_PATTERN.finditer(md):
        url = urllib.parse.urlparse(m.group('url'))
        p = base_dir.joinpath(url.path)
        p.parent.mkdir(parents=True, exist_ok=True)
        if url.fragment == 'cldfviz.map':
            args = [str(ds.tablegroup._fname)]
            kw = urllib.parse.parse_qs(url.query, keep_blank_values=True)
            kw['output'] = [str(p)]
            kw['format'] = [p.suffix[1:].lower()]
            for k, v in kw.items():
                if k in ['pacific-centered', 'language-labels', 'no-legend']:
                    args.append('--' + k)
                else:
                    args.extend(['--' + k, v[0]])
            p = argparse.ArgumentParser()
            map.register(p)
            args = p.parse_args(args)
            args.log = oargs.log
            map.run(args)
