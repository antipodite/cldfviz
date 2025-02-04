"""

"""
import pathlib
import argparse

from clldutils.clilib import PathType
from pycldf import Dataset
from termcolor import colored

from cldfviz.text import iter_templates, render, iter_cldf_image_links
from cldfviz.cli_util import add_testable
from . import map


def get_dataset(p):
    try:
        return Dataset.from_metadata(p) if p.suffix == '.json' else Dataset.from_data(p)
    except ValueError:
        raise argparse.ArgumentTypeError('Invalid CLDF dataset spec: {0}!'.format(p))


def register(parser):
    add_testable(parser)
    parser.add_argument(
        'datasets',
        type=lambda s: (
            get_dataset(PathType(must_exist=True, type='file')(s.split('#')[0])),
            s.partition('#')[2] or None),
        nargs='+',
    )
    parser.add_argument('-l', '--list', help='list templates', default=False, action='store_true')
    parser.add_argument('--text-string', default=None)
    parser.add_argument('--text-file', type=PathType(type='file', must_exist=True), default=None)
    parser.add_argument('--templates', type=PathType(type='dir'), default=None)
    parser.add_argument('--output', type=PathType(type='file', must_exist=False), default=None)


def run(args):
    if len(args.datasets) > 1:
        dss = {prefix or str(i): ds for i, (ds, prefix) in enumerate(args.datasets, start=1)}
    else:
        dss = {args.datasets[0][1]: args.datasets[0][0]}

    if args.list:
        print(colored('Available templates:', attrs=['bold', 'underline']) + '\n')
        for p, doc, vars in iter_templates():
            component, _, type_ = p.stem.partition('_')
            if (component == 'Source' and any(ds.sources for ds in dss.values())) or \
                    any(component in ds for ds in dss.values()):
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
        args.text_string or args.text_file.read_text(encoding='utf8'), dss, args.templates)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(res, encoding='utf8')
        args.log.info('{} written'.format(args.output))

    create_maps(
        args,
        res,
        dss,
        args.output.parent if args.output
        else (pathlib.Path('.') if args.text_string else args.text_file.parent))

    if not args.output:
        print(res)


def create_maps(oargs, md, dss, base_dir):
    for prefix, ds in dss.items():
        for ml in iter_cldf_image_links(md):
            if prefix is None or (ml.parsed_url.fragment.partition('-')[2] == prefix):
                p = base_dir.joinpath(ml.parsed_url.path)
                p.parent.mkdir(parents=True, exist_ok=True)
                args = [str(ds.tablegroup._fname)]
                kw = ml.parsed_url_query
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
                if oargs.test:
                    args.test = True
                args.log = oargs.log
                map.run(args)
