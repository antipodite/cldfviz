import logging

import pytest

from cldfbench.__main__ import main

from cldfviz.map import WITH_CARTOPY, MarkerFactory, leaflet, mpl


@pytest.fixture
def ds_arg(StructureDataset):
    return str(StructureDataset.directory / 'StructureDataset-metadata.json')


def test_text(ds_arg, capsys):
    main(['cldfviz.text', '--text-string', '"[](Source?with_the_works=false#cldf:__all__)"', ds_arg])
    assert 'Peterson, John' in capsys.readouterr()[0]
    main(['cldfviz.text', '-l', ds_arg])
    assert 'CodeTable' in capsys.readouterr()[0]


def test_text_invalid(StructureDataset):
    with pytest.raises(SystemExit):
        main([
            'cldfviz.text', '--text-string', '"a"', str(StructureDataset.directory / 'sources.bib')])


def test_text_multi_ds(ds_arg, capsys):
    main([
        'cldfviz.text',
        '--text-string', '"[](ParameterTable#cldf-p1:B) [](ParameterTable#cldf-p2:D)"',
        ds_arg + '#p1',
        ds_arg + '#p2',
    ])
    out = capsys.readouterr()[0]
    assert 'Gender' in out and 'Oblique' in out


def test_text_with_map(ds_arg, capsys, tmp_path):
    tmpl = tmp_path / 'templ.md'
    tmpl.write_text('![](map.html?parameters=B&pacific-centered#cldfviz.map-pref)')
    main(['cldfviz.text', '--text-file', str(tmpl), '--test', '--output', str(tmp_path / 'test.md'), ds_arg + '#pref'])
    assert tmp_path.joinpath('map.html').exists()


class MF(MarkerFactory):
    def __init__(self, ds, args, param):
        MarkerFactory.__init__(self, ds, args, param)
        assert param == 'test'

    def __call__(self, map, language, values, colormaps):
        if self.args.format == 'html':
            return leaflet.LeafletMarkerSpec(css='.leaflet-tooltip {}')
        return mpl.MPLMarkerSpec(text='text')


def test_map(glottolog_dir, tmp_path, capsys, ds_arg, md_path_factory):
    values = tmp_path.joinpath('values.csv')
    values.write_text("""\
ID,Language_ID,Parameter_ID,Value
1,abcd1235,param1,val1
2,abcd1234,param1,val2
3,book1243,param1,val3
5,book1243,param2,val3
4,isol1234,param1,val4""", encoding='utf8')
    sd = ds_arg

    def run(data=None, **kw):
        for k, v in dict(
            glottolog=glottolog_dir,
            output=tmp_path / 'testmap',
            format='html',
            test=None,
        ).items():
            kw.setdefault(k, v)
        args = ['cldfviz.map']
        for k, v in kw.items():
            args.append('--{}'.format(k.replace('_', '-')))
            if v is not None:
                args.append(str(v))
        args.append(str(data or values))
        main(args, log=logging.getLogger(__name__))

    run(parameters='param1')
    assert tmp_path.joinpath('testmap.html').exists()

    run(parameters='param1',
        colormaps='{"val1": "#a00", "val2": "#0a0", "val3": "#00a", "val4": "#000"}')
    assert tmp_path.joinpath('testmap.html').exists()

    with pytest.raises(SystemExit):  # Shapes in colormap, but just one parameter.
        run(parameters='param1',
            colormaps='{"val1": "circle", "val2": "#0a0", "val3": "#00a", "val4": "#000"}')

    with pytest.raises(SystemExit):  # Explicit color map for non-categorical parameter.
        run(parameters='B',
            colormaps='{"v":"#aaaaaa"}',
            data=sd)

    with pytest.raises(SystemExit):  # Shapes in color maps for both parameters.
        run(parameters='C,D',
            colormaps='{"0":"circle","1":"diamond","2":"square"},'
                      '{"0":"circle","1":"diamond","2":"square"}',
            data=sd)

    run(parameters='C,D',
        colormaps='{"0":"circle","1":"diamond","2":"square"},tol',
        data=sd)

    with pytest.raises(SystemExit):
        # Non-matching colormap values:
        run(parameters='param1', colormaps='{"x": "y"}')
    out, _ = capsys.readouterr()
    assert 'ERROR' in out

    run(parameters='B,C',
        colormaps='viridis,tol',
        language_properties='Family_name',
        pacific_centered=None,
        data=str(md_path_factory('StructureDataset_listvalued_glottocode')))
    assert tmp_path.joinpath('testmap.html').exists()

    run(marker_factory='cldfviz.map', data=sd)
    run(marker_factory='{},test'.format(__file__), data=sd)

    if WITH_CARTOPY:
        run(format='png', parameters='param1')
        assert tmp_path.joinpath('testmap.png').exists()
        run(format='jpg',
            title='The Title',
            language_labels=None,
            parameters='B,C',
            colormaps='viridis,tol',
            language_properties='Family_name',
            pacific_centered=None,
            output=tmp_path / 'testmap.jpg',
            data=sd)
        assert tmp_path.joinpath('testmap.jpg').exists()

        run(format='png', projection='Robinson', parameters='param1', with_stock_img=None)
        run(format='png', projection='Robinson', parameters='param1', extent='"-150,150,50,-50"')
        run(format='png', projection='Robinson', parameters='param1', zorder='{"v":5}')
        run(format='png', projection='Robinson', parameters='param1,param2', no_borders=None)
        run(format='png', marker_factory='cldfviz.map', data=sd)
        run(format='png', marker_factory='{},test'.format(__file__), data=sd)
        run(format='png',
            data=sd,
            parameters='C,D',
            colormaps='{"0":"circle","1":"diamond","2":"square"},tol')
        run(format='png',
            data=sd,
            parameters='C,D',
            colormaps='{"0":"circle","1":"diamond","2":"square"},tol',
            projection='Mollweide')
